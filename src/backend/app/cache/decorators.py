"""缓存装饰器 —— 对 Service 方法透明地添加 Redis 缓存。"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable

from app.cache.client import get_redis

logger = logging.getLogger(__name__)


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """根据函数参数生成缓存 key。跳过 db session 参数。"""
    key_parts = {"args": [], "kwargs": {}}
    for a in args:
        # 跳过 SQLAlchemy AsyncSession（无法序列化且不参与业务语义）
        type_name = type(a).__module__
        if "sqlalchemy" in type_name:
            continue
        key_parts["args"].append(str(a))
    for k, v in kwargs.items():
        type_name = type(v).__module__
        if "sqlalchemy" in type_name:
            continue
        key_parts["kwargs"][k] = str(v)
    raw = json.dumps(key_parts, sort_keys=True)
    digest = hashlib.md5(raw.encode()).hexdigest()[:16]
    return f"cache:{prefix}:{digest}"


def cache_result(ttl: int = 300):
    """缓存异步函数的返回值到 Redis。

    Args:
        ttl: 缓存过期时间（秒），默认 5 分钟。

    Usage:
        @cache_result(ttl=120)
        async def list_tours(self, db, *, locale, page, ...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                redis = await get_redis()
            except Exception:
                return await func(*args, **kwargs)

            cache_key = _make_cache_key(func.__qualname__, *args, **kwargs)

            try:
                cached = await redis.get(cache_key)
                if cached is not None:
                    data = json.loads(cached)
                    # 尝试用 Pydantic model_validate 重建
                    return _rebuild_response(func, data)
            except Exception:
                pass

            result = await func(*args, **kwargs)

            try:
                serialized = _serialize_result(result)
                await redis.setex(cache_key, ttl, json.dumps(serialized, default=str))
            except Exception:
                pass

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """删除匹配 pattern 的缓存 key。通常在写操作后调用。"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            try:
                redis = await get_redis()
                keys = []
                async for key in redis.scan_iter(match=f"cache:{pattern}:*"):
                    keys.append(key)
                if keys:
                    await redis.delete(*keys)
            except Exception:
                pass
            return result

        return wrapper

    return decorator


def _serialize_result(result: Any) -> Any:
    """将 Pydantic 模型或列表递归转为 dict。"""
    if result is None:
        return None
    if hasattr(result, "model_dump"):
        return {"__pydantic__": type(result).__name__, "data": result.model_dump()}
    if isinstance(result, list):
        return [_serialize_result(item) for item in result]
    if isinstance(result, dict):
        return {k: _serialize_result(v) for k, v in result.items()}
    return result


def _rebuild_response(func: Callable, data: Any) -> Any:
    """从缓存数据重建 Pydantic 响应对象。"""
    if isinstance(data, dict) and "__pydantic__" in data:
        import importlib

        # 从返回注解推断模型类
        hints = func.__annotations__
        return_type = hints.get("return")
        if return_type is not None:
            try:
                return return_type(**data["data"])
            except Exception:
                pass
    return data
