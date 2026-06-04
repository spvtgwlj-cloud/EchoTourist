"""Elasticsearch 异步客户端管理。"""

import logging

from elasticsearch import AsyncElasticsearch

from app.config import settings

logger = logging.getLogger(__name__)

_es_client: AsyncElasticsearch | None = None


async def get_es() -> AsyncElasticsearch:
    """获取 ES 客户端（延迟初始化）。"""
    global _es_client
    if _es_client is None:
        _es_client = AsyncElasticsearch(
            settings.elasticsearch_url,
            request_timeout=10,
            max_retries=2,
            retry_on_timeout=True,
        )
    return _es_client


async def close_es():
    """关闭 ES 连接。"""
    global _es_client
    if _es_client:
        await _es_client.close()
        _es_client = None


async def check_es_health() -> bool:
    """检查 ES 是否可用。"""
    try:
        es = await get_es()
        info = await es.info()
        return True
    except Exception:
        logger.warning("Elasticsearch is not available; search will be disabled")
        return False
