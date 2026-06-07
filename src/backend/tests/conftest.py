"""测试夹具（Fixtures）和共享工具。

设计说明：
- API 集成测试通过 httpx 请求运行中的 Docker 服务（http://localhost:8000）
- 单元测试（CRUD/Service）= 直接使用数据库 session
- 每个 API 测试函数结束后自动清理可变数据（订单/评价/收藏），互不干扰
"""

import uuid
import asyncio
import redis as sync_redis
from datetime import datetime, date, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.config import settings
from app.models.user import User
from app.models.tour import Tour, TourTranslation, TourDate, TourImage
from app.models.attraction import Attraction, AttractionTranslation
from app.models.attraction_ticket import AttractionTicket
from app.models.attraction_wishlist import AttractionWishlist
from app.models.destination import Destination
from app.models.order import Order, OrderPassenger
from app.core.security import hash_password, create_access_token


# ============================================================
# 数据库夹具
# ============================================================

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """session scoped 事件循环。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """每个测试独立引擎，避免 asyncpg 连接池冲突。"""
    engine = create_async_engine(settings.database_url, echo=False, pool_size=2)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """每个测试一个独立 session（CRUD/Service 测试使用）。"""
    async with async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )() as session:
        yield session


# ============================================================
# API 集成测试客户端
# ============================================================

@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """使用运行中的 Docker 容器服务进行集成测试。"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client


# ============================================================
# 自动数据清理 — 解决共享数据库测试隔离问题
# ============================================================

@pytest_asyncio.fixture(autouse=True)
async def auto_cleanup():
    """每个 API 测试执行前重置可变数据到基线状态。

    原因：API 集成测试共享同一个 PostgreSQL 数据库，
    前一个测试创建的订单/评价/收藏会干扰后一个测试。
    这个 fixture 在每次测试前重置这些可变数据，
    确保每个测试看到的是干净的数据库状态。

    重置内容：
    - 团期库存 → 15（种子数据基线值）
    - 删除所有订单 / 订单乘客 / 评价 / 收藏
    - 清空 Redis 缓存（避免跨测试的过期 tour list 缓存）

    不受影响的数据：tours, users, destinations（种子数据）。
    """
    # 测试前清理：确保每个测试从干净状态开始
    engine = create_async_engine(settings.database_url, echo=False, pool_size=1)
    try:
        async with engine.connect() as conn:
            await conn.execute(text(
                "UPDATE tour_dates SET availability = 15 WHERE status = 'available'"
            ))
            await conn.execute(text("DELETE FROM order_passengers"))
            await conn.execute(text("DELETE FROM orders"))
            await conn.execute(text("DELETE FROM reviews"))
            await conn.execute(text("DELETE FROM wishlists"))
            await conn.execute(text("DELETE FROM attraction_wishlists"))
            await conn.commit()
    finally:
        await engine.dispose()

    # 清空 Redis 缓存，防止 @cache_result 返回过期数据干扰测试
    # 注意：使用同步 Redis 客户端避免 async event loop 生命周期问题
    try:
        sr = sync_redis.from_url(settings.redis_url)
        keys = sr.keys("cache:*")
        if keys:
            sr.delete(*keys)
        sr.close()
    except Exception as e:
        print(f"[auto_cleanup] Redis cache clear failed: {e}")

    yield


# ============================================================
# 测试数据工厂
# ============================================================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """创建测试用户。"""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        name="Test User",
        hashed_password=hash_password("testpass123"),
        is_active=True,
        is_admin=False,
        locale="en",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """创建管理员测试用户。"""
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=email,
        name="Admin User",
        hashed_password=hash_password("adminpass123"),
        is_active=True,
        is_admin=True,
        locale="en",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """返回 JWT 认证头。"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_tour(db_session: AsyncSession) -> Tour:
    """创建完整的测试旅游产品（含翻译/日期/图片）。"""
    tour_id = uuid.uuid4()
    tour = Tour(
        id=tour_id,
        slug=f"test-tour-{uuid.uuid4().hex[:6]}",
        status="published",
        type="group_tour",
        duration_days=7,
        duration_nights=6,
        max_pax=20,
        min_pax=2,
        start_price=1200.00,
        currency="USD",
        difficulty="moderate",
        theme="adventure",
        highlights=["Mountain hiking", "Cultural experience"],
        includes=["Hotel", "Guide"],
        excludes=["Flights"],
        destination_ids=[uuid.uuid4()],
        avg_rating=4.5,
        review_count=10,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(tour)

    # 英文翻译
    db_session.add(TourTranslation(
        id=uuid.uuid4(),
        tour_id=tour_id,
        locale="en",
        name="Test Great Tour",
        subtitle="An amazing test tour",
        description="This is a comprehensive test tour with amazing experiences.",
        itinerary=[
            {"day": 1, "title": "Arrival", "description": "Arrive and check in",
             "meals": ["Dinner"]},
            {"day": 2, "title": "Exploration", "description": "Full day exploration",
             "meals": ["Breakfast", "Lunch", "Dinner"]},
        ],
    ))
    # 中文翻译
    db_session.add(TourTranslation(
        id=uuid.uuid4(),
        tour_id=tour_id,
        locale="zh",
        name="测试精彩之旅",
        subtitle="一次精彩的测试之旅",
        description="这是一个全面的测试旅游产品，提供令人惊叹的体验。",
    ))
    # 日期 x3
    for i in range(3):
        start = date.today() + timedelta(days=30 * (i + 1))
        db_session.add(TourDate(
            id=uuid.uuid4(), tour_id=tour_id,
            start_date=start, end_date=start + timedelta(days=6),
            price_per_pax=1200.00 + (i * 50), currency="USD",
            availability=15, status="available",
        ))
    # 图片
    db_session.add(TourImage(
        id=uuid.uuid4(), tour_id=tour_id,
        url="https://example.com/image.jpg", alt_text="Test image", sort_order=0,
    ))

    await db_session.flush()
    return tour


@pytest_asyncio.fixture
async def test_tour_date(test_tour: Tour, db_session: AsyncSession) -> TourDate:
    """测试 tour 的第一个可预订日期。"""
    result = await db_session.execute(
        select(TourDate).where(
            TourDate.tour_id == test_tour.id,
            TourDate.status == "available",
        ).order_by(TourDate.start_date)
    )
    return result.scalars().first()


# ============================================================
# 辅助类
# ============================================================

class TestDataFactory:
    @staticmethod
    def valid_register_data() -> dict:
        return {
            "email": f"new_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePass123!",
            "name": "New User",
        }

    @staticmethod
    def login_data(email: str, password: str = "testpass123") -> dict:
        return {"email": email, "password": password}


@pytest.fixture
def factory() -> TestDataFactory:
    return TestDataFactory()


# ============================================================
# 景点（Attraction）相关 fixtures
# ============================================================

@pytest_asyncio.fixture
async def test_destination(db_session: AsyncSession) -> Destination:
    """创建测试目的地。"""
    dest = Destination(
        id=uuid.uuid4(),
        slug=f"test-dest-{uuid.uuid4().hex[:6]}",
        status="active",
    )
    db_session.add(dest)
    await db_session.flush()
    return dest


@pytest_asyncio.fixture
async def test_attraction(
    db_session: AsyncSession, test_destination: Destination
) -> Attraction:
    """创建测试景点（含翻译和门票类型）。"""
    aid = uuid.uuid4()
    attr = Attraction(
        id=aid,
        slug=f"test-attr-{uuid.uuid4().hex[:6]}",
        destination_id=test_destination.id,
        image_url="https://example.com/attr.jpg",
        sort_order=1,
        rating=4,
        ticket_price=50.00,
        ticket_currency="USD",
        status="active",
    )
    db_session.add(attr)
    # 英文翻译
    db_session.add(AttractionTranslation(
        id=uuid.uuid4(),
        attraction_id=aid,
        locale="en",
        name="Test Attraction",
        description="A test attraction for unit testing",
        ticket_info="Standard entry",
    ))
    # 中文翻译
    db_session.add(AttractionTranslation(
        id=uuid.uuid4(),
        attraction_id=aid,
        locale="zh",
        name="测试景点",
        description="用于单元测试的测试景点",
    ))
    # 门票类型 x2
    db_session.add(AttractionTicket(
        id=uuid.uuid4(),
        attraction_id=aid,
        ticket_type="standard",
        price=50.00,
        currency="USD",
        availability=100,
        status="available",
    ))
    db_session.add(AttractionTicket(
        id=uuid.uuid4(),
        attraction_id=aid,
        ticket_type="vip",
        price=100.00,
        currency="USD",
        availability=20,
        status="available",
    ))
    await db_session.flush()
    return attr
