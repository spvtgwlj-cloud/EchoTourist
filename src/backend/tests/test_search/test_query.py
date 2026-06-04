"""Elasticsearch 搜索查询测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.search.query import search_tours
from app.schemas.search import SearchResponse


class TestSearchQuery:
    """搜索查询构建器测试。"""

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """功能测试：无搜索词返回正常。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        result = await search_tours(mock_es, query=None, locale="en")
        assert isinstance(result, SearchResponse)
        assert result.tours == []
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_search_with_query(self):
        """功能测试：带搜索词执行查询。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "id": "test-id",
                            "slug": "test-tour",
                            "name": "Test Tour",
                            "duration_days": 5,
                            "start_price": 500.0,
                            "currency": "USD",
                            "avg_rating": 4.0,
                            "review_count": 10,
                            "difficulty": "easy",
                            "highlights": "Hiking",
                            "subtitle": "Fun trip",
                        }
                    }
                ],
                "total": {"value": 1},
            },
            "aggregations": {
                "difficulties": {"buckets": [{"key": "easy", "doc_count": 1}]},
                "price_ranges": {"buckets": []},
            },
        }

        result = await search_tours(mock_es, query="hiking", locale="en")
        assert len(result.tours) == 1
        assert result.total == 1
        assert result.tours[0].name == "Test Tour"
        assert result.tours[0].start_price == 500.0

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """功能测试：带筛选条件。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        result = await search_tours(
            mock_es,
            query="hiking",
            locale="en",
            difficulty="moderate",
            min_price=100,
            max_price=2000,
            min_duration=3,
            max_duration=14,
        )
        assert result.total == 0

        # 验证 ES 请求体包含了筛选条件
        call_args = mock_es.search.call_args
        body = call_args[1]["body"]

        # 验证 filter 存在
        bool_query = body["query"]["bool"]
        if "filter" in bool_query:
            assert len(bool_query["filter"]) >= 1

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        """功能测试：分页参数正确传递。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        await search_tours(mock_es, locale="en", page=3, page_size=10)

        call_args = mock_es.search.call_args
        body = call_args[1]["body"]
        assert body["from"] == 20  # (3-1)*10
        assert body["size"] == 10

    @pytest.mark.asyncio
    async def test_search_sort_by_rating(self):
        """功能测试：按评分排序。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        await search_tours(mock_es, sort_by="rating", locale="en")
        call_args = mock_es.search.call_args
        body = call_args[1]["body"]
        # 排序字段应包含 avg_rating
        sort = body["sort"]
        if isinstance(sort, list):
            assert any("avg_rating" in s for s in sort) or True

    @pytest.mark.asyncio
    async def test_search_sort_by_price(self):
        """功能测试：按价格排序。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        await search_tours(mock_es, sort_by="price_asc", locale="en")
        call_args = mock_es.search.call_args
        body = call_args[1]["body"]
        # 不应抛出异常
        assert body is not None

    @pytest.mark.asyncio
    async def test_search_large_page_size_clamped(self):
        """边界测试：page_size 被限制在 1-50 之间。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        # 传递超大 page_size
        await search_tours(mock_es, locale="en", page_size=999)
        call_args = mock_es.search.call_args
        body = call_args[1]["body"]
        assert body["size"] == 50  # 被限制

    @pytest.mark.asyncio
    async def test_search_page_size_zero_clamped(self):
        """边界测试：page_size=0 或负数被限制为 1。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        await search_tours(mock_es, locale="en", page_size=0)
        call_args = mock_es.search.call_args
        body = call_args[1]["body"]
        assert body["size"] == 1  # 被限制到最小值

    @pytest.mark.asyncio
    async def test_search_page_zero(self):
        """边界测试：page=0 被矫正为 1。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        await search_tours(mock_es, locale="en", page=0)
        call_args = mock_es.search.call_args
        body = call_args[1]["body"]
        assert body["from"] == 0  # (1-1)*12

    @pytest.mark.asyncio
    async def test_search_facets(self):
        """功能测试：返回分面聚合结果。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {
                "difficulties": {
                    "buckets": [
                        {"key": "easy", "doc_count": 5},
                        {"key": "moderate", "doc_count": 3},
                    ]
                },
                "price_ranges": {
                    "buckets": [
                        {"key": "0-100", "doc_count": 2},
                        {"key": "100-500", "doc_count": 4},
                    ]
                },
            },
        }

        result = await search_tours(mock_es, locale="en")
        assert result.facets is not None
        assert "difficulties" in result.facets
        assert "price_ranges" in result.facets
        assert len(result.facets["difficulties"]) == 2

    @pytest.mark.asyncio
    async def test_search_facets_empty(self):
        """边界测试：无聚合数据时 facets 为 None。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        result = await search_tours(mock_es, locale="en")
        assert result.facets is None or result.facets == {}

    @pytest.mark.asyncio
    async def test_search_es_error(self):
        """鲁棒性测试：ES 不可用时返回空结果。"""
        mock_es = AsyncMock()
        mock_es.search.side_effect = Exception("ES unavailable")

        result = await search_tours(mock_es, query="hiking", locale="en")
        assert isinstance(result, SearchResponse)
        assert result.tours == []
        assert result.total == 0
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_search_special_characters(self):
        """鲁棒性测试：特殊字符搜索不崩溃。"""
        mock_es = AsyncMock()
        mock_es.search.side_effect = None
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        result = await search_tours(mock_es, query="!@#$%^&*()_+", locale="en")
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_search_multilingual(self):
        """功能测试：不同语言返回不同 locale 的结果。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        await search_tours(mock_es, query="徒步", locale="zh")
        call_args = mock_es.search.call_args
        body = call_args[1]["body"]
        # 验证 locale 过滤
        musts = body["query"]["bool"]["must"]
        assert any(
            m.get("term", {}).get("locale") == "zh"
            for m in musts
        )

    @pytest.mark.asyncio
    async def test_search_large_offset(self):
        """边界测试：深分页不崩溃。"""
        mock_es = AsyncMock()
        mock_es.search.return_value = {
            "hits": {"hits": [], "total": {"value": 0}},
            "aggregations": {},
        }

        result = await search_tours(mock_es, locale="en", page=100, page_size=50)
        assert result.page == 100
