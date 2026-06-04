"""Elasticsearch 索引 Celery 任务。"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="app.tasks.search_tasks.reindex_all_tours",
    max_retries=2,
    default_retry_delay=60,
)
def reindex_all_tours() -> int:
    """异步重建所有旅游产品的 ES 索引。"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from app.database import async_session
        from app.search.client import get_es
        from app.search.index import bulk_index_tours

        async def _run():
            es = await get_es()
            async with async_session() as db:
                return await bulk_index_tours(db, es)

        count = loop.run_until_complete(_run())
        logger.info(f"Reindexed {count} tours")
        return count
    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        return 0
    finally:
        loop.close()
