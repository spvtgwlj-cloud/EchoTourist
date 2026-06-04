"""Redis 异步连接管理。"""

import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """获取 Redis 连接实例（延迟初始化）。"""
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis


async def close_redis():
    """关闭 Redis 连接。"""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
