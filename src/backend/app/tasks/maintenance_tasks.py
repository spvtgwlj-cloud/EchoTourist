"""定期维护 Celery 任务。"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.maintenance_tasks.cleanup_expired_sessions")
def cleanup_expired_sessions() -> int:
    """清除过期的 Redis session。"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            from app.cache.client import get_redis
            redis = await get_redis()
            count = 0
            async for key in redis.scan_iter(match="cache:*"):
                ttl = await redis.ttl(key)
                if ttl < 0:  # expired
                    await redis.delete(key)
                    count += 1
            return count

        result = loop.run_until_complete(_run())
        logger.info(f"Cleaned up {result} expired cache keys")
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 0
