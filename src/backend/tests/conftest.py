"""测试夹具（Fixtures）和共享工具。

设计说明：
- API 集成测试 = 通过 httpx 直接请求运行中的 Docker 服务（http://localhost:8000）
- 单元测试（CRUD/Service）= 直接使用数据库 session
"""

import uuid
import asyncio
from datetime import datetime, date, timedelta, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.config import settings
from app.models.user import User
from app.models.tour import Tour, TourTranslation, TourDate, TourImage
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
    """每个测试一个独立 session。"""
    async with async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )() as session:
        yield session


# ============================================================
# API 集成测试客户端（直连运行中的 Docker 服务）
# ============================================================

@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """使用运行中的 Docker 容器服务进行集成测试。"""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        yield client


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
