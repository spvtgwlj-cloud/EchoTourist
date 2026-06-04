"""Redis 缓存装饰器测试。"""

import json

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.cache.decorators import _make_cache_key, cache_result, invalidate_cache


# ============================================================
# 辅助：创建带 __qualname__ 的 mock async 函数
# ============================================================

async def _make_mock_func(return_value="result"):
    """创建 AsyncMock 并设定 __qualname__ 属性。"""
    m = AsyncMock(return_value=return_value)
    m.__qualname__ = "test_mock_function"
    return m


# ============================================================
# Key 生成
# ============================================================

class TestCacheKeyGeneration:

    def test_cache_key_from_args(self):
        key = _make_cache_key("test_func", "arg1", "arg2")
        assert key.startswith("cache:test_func:")
        assert len(key) > 20

    def test_cache_key_from_kwargs(self):
        key = _make_cache_key("test_func", locale="en", page=1)
        assert key.startswith("cache:test_func:")

    def test_cache_key_skips_db_session(self):
        class MockSession:
            __module__ = "sqlalchemy.ext.asyncio"
        session = MockSession()
        key1 = _make_cache_key("test_func", session, locale="en")
        key2 = _make_cache_key("test_func", locale="en")
        assert key1 == key2

    def test_cache_key_deterministic(self):
        key1 = _make_cache_key("test_func", locale="en", page=1)
        key2 = _make_cache_key("test_func", locale="en", page=1)
        assert key1 == key2

    def test_cache_key_different_params(self):
        key1 = _make_cache_key("test_func", locale="en", page=1)
        key2 = _make_cache_key("test_func", locale="zh", page=1)
        assert key1 != key2

    def test_cache_key_with_no_args(self):
        key = _make_cache_key("simple_func")
        assert key.startswith("cache:simple_func:")

    def test_cache_key_unicode(self):
        key = _make_cache_key("search_func", query="北京 长城")
        assert key.startswith("cache:search_func:")

    def test_cache_key_none_value(self):
        key = _make_cache_key("func", param=None)
        assert key.startswith("cache:func:")


# ============================================================
# @cache_result 装饰器
# ============================================================

class TestCacheResultDecorator:

    @pytest.mark.asyncio
    async def test_cache_miss_calls_function(self):
        """缓存未命中时调用原函数。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        mock_func = await _make_mock_func({"result": "fresh"})

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = cache_result(ttl=60)(mock_func)
            result = await decorated()

        assert result == {"result": "fresh"}
        mock_func.assert_awaited_once()
        mock_redis.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_hit_skips_function(self):
        """缓存命中时不调用原函数。"""
        cached_data = json.dumps({"result": "cached"})
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=cached_data)
        mock_redis.setex = AsyncMock()

        mock_func = await _make_mock_func("should not be called")

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = cache_result(ttl=60)(mock_func)
            result = await decorated()

        mock_func.assert_not_awaited()
        assert result == {"result": "cached"}

    @pytest.mark.asyncio
    async def test_cache_redis_unavailable(self):
        """Redis 不可用时回退到原函数。"""
        mock_func = await _make_mock_func({"result": "fallback"})

        with patch("app.cache.decorators.get_redis", side_effect=Exception("Redis down")):
            decorated = cache_result(ttl=60)(mock_func)
            result = await decorated()

        assert result == {"result": "fallback"}
        mock_func.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_redis_setex_fails_still_returns(self):
        """存储缓存失败时仍返回函数结果。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(side_effect=Exception("setex failed"))

        mock_func = await _make_mock_func({"result": "ok"})

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = cache_result(ttl=60)(mock_func)
            result = await decorated()

        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_cache_custom_ttl(self):
        """自定义 TTL 传递到 setex。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        mock_func = await _make_mock_func("result")

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = cache_result(ttl=999)(mock_func)
            await decorated()

        mock_redis.setex.assert_awaited_once()
        args, _ = mock_redis.setex.call_args
        assert args[1] == 999

    @pytest.mark.asyncio
    async def test_cache_zero_ttl(self):
        """边界测试：TTL=0 仍然调用 setex。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        mock_func = await _make_mock_func("zero_ttl")

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = cache_result(ttl=0)(mock_func)
            result = await decorated()

        assert result == "zero_ttl"
        mock_redis.setex.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_large_return_value(self):
        """边界测试：大返回值序列化。"""
        large_data = {"key": "x" * 10000}
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        mock_func = await _make_mock_func(large_data)

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = cache_result(ttl=60)(mock_func)
            result = await decorated()

        assert result == large_data

    @pytest.mark.asyncio
    async def test_cache_corrupted_data_ignored(self):
        """鲁棒性测试：损坏的缓存数据被忽略，重新计算。"""
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="not valid json {{")
        mock_redis.setex = AsyncMock()

        mock_func = await _make_mock_func({"result": "recomputed"})

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = cache_result(ttl=60)(mock_func)
            result = await decorated()

        assert result == {"result": "recomputed"}
        mock_func.assert_awaited_once()


# ============================================================
# @invalidate_cache 装饰器
# ============================================================

class TestInvalidateCache:

    @pytest.mark.asyncio
    async def test_invalidate_matching_keys(self):
        """删除匹配 pattern 的 key。"""
        mock_redis = MagicMock()

        async def mock_scan_iter(match):
            yield "cache:tour:key1"
            yield "cache:tour:key2"

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = AsyncMock(return_value=2)

        mock_func = await _make_mock_func("deleted")

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = invalidate_cache("tour")(mock_func)
            result = await decorated()

        assert result == "deleted"
        mock_redis.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalidate_no_matching_keys(self):
        """无匹配 key 时不调用 delete。"""
        mock_redis = MagicMock()

        async def empty_iter(match):
            return
            yield

        mock_redis.scan_iter = empty_iter
        mock_redis.delete = AsyncMock()

        mock_func = await _make_mock_func("result")

        with patch("app.cache.decorators.get_redis", return_value=mock_redis):
            decorated = invalidate_cache("nonexistent")(mock_func)
            result = await decorated()

        assert result == "result"
        mock_redis.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_invalidate_redis_unavailable(self):
        """Redis 不可用时不影响原函数。"""
        mock_func = await _make_mock_func("result")

        with patch("app.cache.decorators.get_redis", side_effect=Exception("Redis down")):
            decorated = invalidate_cache("tour")(mock_func)
            result = await decorated()

        assert result == "result"
