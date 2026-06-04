"""Elasticsearch 索引管理测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.search.index import (
    INDEX_NAME,
    INDEX_MAPPING,
    create_index,
    delete_index,
    index_tour,
)


class TestIndexDefinition:
    """索引映射定义测试。"""

    def test_index_name(self):
        """功能测试：索引名称正确。"""
        assert INDEX_NAME == "tours"

    def test_index_mapping_has_settings(self):
        """功能测试：映射包含 settings。"""
        assert "settings" in INDEX_MAPPING

    def test_index_mapping_has_mappings(self):
        """功能测试：映射包含 mappings。"""
        assert "mappings" in INDEX_MAPPING

    def test_index_mapping_key_fields_present(self):
        """功能测试：映射包含必要的核心字段。"""
        props = INDEX_MAPPING["mappings"]["properties"]
        for field in ["id", "slug", "name", "description", "duration_days",
                       "start_price", "difficulty", "locale", "status"]:
            assert field in props, f"Missing field: {field}"

    def test_index_mapping_name_is_text(self):
        """功能测试：name 字段类型为 text。"""
        props = INDEX_MAPPING["mappings"]["properties"]
        assert props["name"]["type"] == "text"

    def test_index_mapping_price_is_float(self):
        """功能测试：价格字段类型正确。"""
        props = INDEX_MAPPING["mappings"]["properties"]
        assert props["start_price"]["type"] == "float"

    def test_index_mapping_shard_count(self):
        """功能测试：分片数合理（开发环境 1）。"""
        settings = INDEX_MAPPING["settings"]
        assert settings["number_of_shards"] == 1

    def test_index_mapping_has_analyzer(self):
        """功能测试：映射定义了分析器。"""
        settings = INDEX_MAPPING["settings"]["analysis"]
        assert "analyzer" in settings
        assert "tours_combined" in settings["analyzer"]


class TestIndexOperations:
    """索引管理操作测试。"""

    @pytest.mark.asyncio
    async def test_create_index_new(self):
        """功能测试：索引不存在时创建。"""
        mock_es = AsyncMock()
        mock_es.indices.exists.return_value = False
        mock_es.indices.create = AsyncMock()

        result = await create_index(mock_es)

        assert result is True
        mock_es.indices.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_index_exists(self):
        """功能测试：索引已存在时跳过。"""
        mock_es = AsyncMock()
        mock_es.indices.exists.return_value = True

        result = await create_index(mock_es)

        assert result is False
        mock_es.indices.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_index_exists(self):
        """功能测试：删除已存在的索引。"""
        mock_es = AsyncMock()
        mock_es.indices.exists.return_value = True
        mock_es.indices.delete = AsyncMock()

        await delete_index(mock_es)

        mock_es.indices.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_index_not_exists(self):
        """边界测试：删除不存在的索引不报错。"""
        mock_es = AsyncMock()
        mock_es.indices.exists.return_value = False

        await delete_index(mock_es)

        mock_es.indices.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_index_error(self):
        """鲁棒性测试：创建索引失败时抛出异常。"""
        mock_es = AsyncMock()
        mock_es.indices.exists.side_effect = Exception("ES connection error")

        with pytest.raises(Exception):
            await create_index(mock_es)

    @pytest.mark.asyncio
    async def test_index_tour(self):
        """功能测试：索引单个 tour 文档。"""
        mock_es = AsyncMock()
        mock_es.index = AsyncMock()

        # 创建 mock tour
        mock_tour = MagicMock()
        mock_tour.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_tour.slug = "test-tour"
        mock_tour.status = "published"
        mock_tour.type = "group_tour"
        mock_tour.duration_days = 7
        mock_tour.start_price = 1000.0
        mock_tour.currency = "USD"
        mock_tour.avg_rating = 4.5
        mock_tour.review_count = 10
        mock_tour.difficulty = "moderate"
        mock_tour.max_pax = 20
        mock_tour.destination_ids = ["uuid-1", "uuid-2"]
        mock_tour.highlights = ["Hiking", "Culture"]
        mock_tour.published_at = None
        mock_tour.created_at = None

        mock_translation = MagicMock()
        mock_translation.locale = "en"
        mock_translation.name = "Test Tour"
        mock_translation.description = "A great tour"
        mock_translation.subtitle = "Amazing"

        await index_tour(mock_es, mock_tour, mock_translation)

        mock_es.index.assert_awaited_once()
        args, kwargs = mock_es.index.call_args
        assert kwargs["index"] == "tours"
        assert "document" in kwargs
        doc = kwargs["document"]
        assert doc["name"] == "Test Tour"
        assert doc["locale"] == "en"


class TestBulkIndex:
    """批量索引测试。"""

    @pytest.mark.asyncio
    async def test_bulk_index_empty_should_not_fail(self):
        """鲁棒性测试：空数据批量索引不崩溃。"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_es = AsyncMock()

        from app.search.index import bulk_index_tours
        count = await bulk_index_tours(mock_db, mock_es)
        assert count == 0
