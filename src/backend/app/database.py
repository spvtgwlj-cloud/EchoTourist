import asyncio
import logging
import os
import subprocess

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库：优先运行 Alembic 迁移，失败时回退到 create_all。"""
    # 尝试运行 Alembic 迁移
    try:
        proc = await asyncio.create_subprocess_exec(
            "alembic", "upgrade", "head",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": "/app"},
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            logger.info("Database migrations applied successfully")
            return
        logger.warning(f"Alembic migration failed (will use create_all): {stderr.decode()[:200]}")
    except Exception as e:
        logger.warning(f"Alembic migration unavailable (will use create_all): {e}")

    # 回退：自动创建表（开发模式）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created via create_all (no migrations)")


async def close_db():
    await engine.dispose()
