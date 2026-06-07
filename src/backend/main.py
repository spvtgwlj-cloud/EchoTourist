import logging
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
from app.database import init_db, close_db
from app.core.error_handlers import register_error_handlers

from app.api.v1.auth import router as auth_router
from app.api.v1.tours import router as tours_router
from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router
from app.api.v1.search import router as search_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.destinations import router as destinations_router
from app.api.v1.wishlist import router as wishlist_router
from app.api.v1.attraction_wishlist import router as attraction_wishlist_router
from app.api.v1.users import router as users_router
from app.api.v1.admin import router as admin_router
from app.api.v1.attractions import router as attractions_router
from app.api.v1.custom_tours import router as custom_tours_router
from app.api.v1.enquiries import router as enquiries_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # 初始化 Elasticsearch 索引（带重试，因为 ES 容器启动较慢）
    es_ready = False
    for attempt in range(5):
        try:
            from app.search.client import get_es, check_es_health
            if await check_es_health():
                es = await get_es()
                from app.search.index import create_index, bulk_index_tours, INDEX_NAME
                await create_index(es)
                logger.info("Elasticsearch index ready")
                es_ready = True
                break
        except Exception:
            if attempt < 4:
                logger.info(f"Waiting for Elasticsearch... (attempt {attempt + 1}/5)")
                await asyncio.sleep(5)
            else:
                logger.warning("Elasticsearch init skipped after 5 attempts")

    # 自动填充 ES 搜索索引数据
    if es_ready:
        try:
            from app.database import async_session
            es = await get_es()
            async with async_session() as db:
                count = await bulk_index_tours(db, es)
                if count > 0:
                    logger.info(f"Auto-indexed {count} tour documents into ES")
                else:
                    logger.info("No published tours to index (ES index may be empty)")
        except Exception as e:
            logger.warning(f"ES auto-indexing skipped: {e}")
    yield
    await close_db()
    # 关闭 Redis / ES 连接
    try:
        from app.cache.client import close_redis
        await close_redis()
    except Exception:
        pass
    try:
        from app.search.client import close_es
        await close_es()
    except Exception:
        pass


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global error handlers
register_error_handlers(app)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 确保静态目录存在并挂载
static_path = Path(settings.static_dir)
static_path.mkdir(parents=True, exist_ok=True)
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(tours_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")
app.include_router(destinations_router, prefix="/api/v1")
app.include_router(wishlist_router, prefix="/api/v1")
app.include_router(attraction_wishlist_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(enquiries_router, prefix="/api/v1")
app.include_router(attractions_router, prefix="/api/v1")
app.include_router(custom_tours_router, prefix="/api/v1")


@app.get("/health")
async def health():
    es_ok = False
    try:
        from app.search.client import check_es_health
        es_ok = await check_es_health()
    except Exception:
        pass

    stripe_configured = bool(settings.stripe_secret_key and settings.stripe_public_key)

    return {
        "status": "ok",
        "version": "0.1.0",
        "elasticsearch": es_ok,
        "stripe_configured": stripe_configured,
        "google_oauth_configured": bool(settings.google_client_id),
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
