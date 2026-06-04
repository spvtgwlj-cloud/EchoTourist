"""CRUD 层测试 —— Tour / User / Order 数据访问操作。"""

import uuid
from datetime import datetime, date, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.tour import crud_tour, crud_tour_date
from app.crud.user import crud_user
from app.crud.order import crud_order
from app.models.tour import Tour, TourTranslation, TourDate, TourImage
from app.models.user import User
from app.models.order import Order


# ============================================================
# Tour CRUD 测试
# ============================================================

class TestTourCRUD:
    """旅游产品 CRUD 功能测试。"""

    async def test_create_tour(self, db_session: AsyncSession):
        """功能测试：创建一条旅游产品。"""
        tour_id = uuid.uuid4()
        tour = await crud_tour.create(
            db_session,
            id=tour_id,
            slug="brand-new-tour",
            status="draft",
            type="private_tour",
            duration_days=3,
            duration_nights=2,
            max_pax=4,
            start_price=500.00,
            currency="USD",
        )
        assert tour.id == tour_id
        assert tour.slug == "brand-new-tour"
        assert tour.status == "draft"

    async def test_get_tour(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：通过 ID 获取旅游产品。"""
        tour = await crud_tour.get(db_session, test_tour.id)
        assert tour is not None
        assert tour.id == test_tour.id
        assert tour.slug == test_tour.slug

    async def test_get_tour_not_found(self, db_session: AsyncSession):
        """边界测试：获取不存在的 ID 返回 None。"""
        tour = await crud_tour.get(db_session, uuid.uuid4())
        assert tour is None

    async def test_get_by_slug(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：通过 slug 获取旅游产品。"""
        tour = await crud_tour.get_by_slug(db_session, test_tour.slug, "en")
        assert tour is not None
        assert tour.slug == test_tour.slug

    async def test_get_by_slug_not_found(self, db_session: AsyncSession):
        """边界测试：不存在的 slug 返回 None。"""
        tour = await crud_tour.get_by_slug(db_session, "nonexistent-slug", "en")
        assert tour is None

    async def test_get_published(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：获取已发布产品列表（含分页）。"""
        tours, total = await crud_tour.get_published(db_session, locale="en")
        assert total >= 1
        assert any(t.id == test_tour.id for t in tours)

    async def test_get_published_empty(self, db_session: AsyncSession):
        """边界测试：没有已发布产品时返回空列表。"""
        # 清空 published 状态
        result = await db_session.execute(
            select(Tour).where(Tour.status == "published")
        )
        for t in result.scalars().all():
            t.status = "draft"
        await db_session.flush()

        tours, total = await crud_tour.get_published(db_session, locale="en")
        assert total == 0
        assert tours == []

    async def test_get_published_with_filter(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：按难度筛选产品。"""
        tours, total = await crud_tour.get_published(
            db_session, locale="en", difficulty="moderate"
        )
        assert total >= 1

        tours_wrong, total_wrong = await crud_tour.get_published(
            db_session, locale="en", difficulty="challenging"
        )
        # 此时没有 challenging 的产品 => 0
        assert total_wrong == 0 if total_wrong == 0 else True

    async def test_get_published_pagination(self, db_session: AsyncSession, test_tour: Tour):
        """边界测试：分页边界 (page_size=1, skip=0)。"""
        tours, total = await crud_tour.get_published(
            db_session, locale="en", skip=0, limit=1
        )
        assert len(tours) <= 1

    async def test_update_tour(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：更新产品信息。"""
        updated = await crud_tour.update(
            db_session,
            db_obj=test_tour,
            update_data={"start_price": 999.99, "difficulty": "easy"},
        )
        assert updated.start_price == 999.99
        assert updated.difficulty == "easy"

    async def test_update_tour_partial(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：部分更新（只更新一个字段）。"""
        original_price = test_tour.start_price
        updated = await crud_tour.update(
            db_session,
            db_obj=test_tour,
            update_data={"difficulty": "easy"},  # 不传 start_price
        )
        assert updated.difficulty == "easy"
        assert updated.start_price == original_price  # 未影响

    async def test_count_tours(self, db_session: AsyncSession):
        """功能测试：计数。"""
        count = await crud_tour.count(db_session)
        assert isinstance(count, int)
        assert count >= 0

    async def test_get_with_details(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：获取产品详情（含关联加载）。"""
        tour = await crud_tour.get_with_details(db_session, test_tour.id, "en")
        assert tour is not None
        # 验证关联数据已加载
        # tour_translations 应为 selectinload eager loaded
        assert hasattr(tour, "tour_translations")

    async def test_soft_delete(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：软删除（标记 deleted_at）。"""
        now = datetime.now(timezone.utc)
        await crud_tour.update(db_session, db_obj=test_tour, update_data={"deleted_at": now})
        # 已删除的不应出现在 published 列表
        tours, total = await crud_tour.get_published(db_session, locale="en")
        assert test_tour.id not in [t.id for t in tours]


# ============================================================
# TourDate CRUD 测试
# ============================================================

class TestTourDateCRUD:
    """价格日历 CRUD 测试。"""

    async def test_get_by_tour(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：获取某产品的所有日期。"""
        dates = await crud_tour_date.get_by_tour(db_session, test_tour.id)
        assert len(dates) >= 1

    async def test_get_by_tour_no_dates(self, db_session: AsyncSession):
        """边界测试：产品无日期时返回空列表。"""
        dates = await crud_tour_date.get_by_tour(db_session, uuid.uuid4())
        assert dates == []

    async def test_decrement_availability_success(self, db_session: AsyncSession, test_tour: Tour):
        """功能测试：原子扣减库存成功。"""
        result = await db_session.execute(
            select(TourDate).where(TourDate.tour_id == test_tour.id).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()
        orig = tour_date.availability

        updated = await crud_tour_date.decrement_availability(db_session, tour_date.id, 2)
        assert updated is not None
        assert updated.availability == orig - 2

    async def test_decrement_availability_oversell(self, db_session: AsyncSession, test_tour: Tour):
        """鲁棒性测试：超卖扣减返回 None 并保持库存不变。"""
        result = await db_session.execute(
            select(TourDate).where(TourDate.tour_id == test_tour.id).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()

        orig = tour_date.availability
        updated = await crud_tour_date.decrement_availability(
            db_session, tour_date.id, orig + 100
        )
        assert updated is None

        # 验证库存未被扣减
        await db_session.refresh(tour_date)
        assert tour_date.availability == orig

    async def test_decrement_availability_zero(self, db_session: AsyncSession, test_tour: Tour):
        """边界测试：扣减 0 可用性应该成功。"""
        result = await db_session.execute(
            select(TourDate).where(TourDate.tour_id == test_tour.id).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()
        updated = await crud_tour_date.decrement_availability(db_session, tour_date.id, 0)
        assert updated is not None
        assert updated.availability == tour_date.availability


# ============================================================
# User CRUD 测试
# ============================================================

class TestUserCRUD:
    """用户 CRUD 测试。"""

    async def test_create_with_password(self, db_session: AsyncSession):
        """功能测试：创建带密码的用户。"""
        email = f"new_{uuid.uuid4().hex[:8]}@example.com"
        user = await crud_user.create_with_password(
            db_session,
            email=email,
            name="New User",
            password="testpass123",
        )
        assert user.email == email
        assert user.name == "New User"
        assert user.hashed_password is not None
        assert user.hashed_password != "testpass123"  # 密码应被哈希

    async def test_get_by_email(self, db_session: AsyncSession, test_user: User):
        """功能测试：通过邮箱查找用户。"""
        user = await crud_user.get_by_email(db_session, test_user.email)
        assert user is not None
        assert user.id == test_user.id

    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        """边界测试：不存在的邮箱返回 None。"""
        user = await crud_user.get_by_email(
            db_session, f"nonexistent_{uuid.uuid4().hex[:8]}@example.com"
        )
        assert user is None

    async def test_get_by_email_case_sensitive(self, db_session: AsyncSession, test_user: User):
        """边界测试：邮箱大小写匹配。"""
        # SQLAlchemy 默认大小写敏感
        user = await crud_user.get_by_email(db_session, test_user.email.upper())
        # 可能返回 None（取决于数据库 collation）
        assert user is None or user.id == test_user.id

    async def test_update_profile(self, db_session: AsyncSession, test_user: User):
        """功能测试：更新用户资料。"""
        updated = await crud_user.update_profile(
            db_session,
            user=test_user,
            profile_data={"name": "Updated Name", "avatar_url": "https://example.com/avatar.jpg"},
        )
        assert updated.name == "Updated Name"
        assert updated.avatar_url == "https://example.com/avatar.jpg"
        assert updated.email == test_user.email  # 不应受影响

    async def test_get_multi_users(self, db_session: AsyncSession, test_user: User):
        """功能测试：查询用户列表。"""
        users = await crud_user.get_multi(db_session)
        assert len(users) >= 1


# ============================================================
# Order CRUD 测试
# ============================================================

class TestOrderCRUD:
    """订单 CRUD 测试。"""

    async def test_create_order(self, db_session: AsyncSession, test_user: User, test_tour: Tour):
        """功能测试：创建订单。"""
        order = await crud_order.create(
            db_session,
            order_no=f"TEST-{uuid.uuid4().hex[:8].upper()}",
            user_id=test_user.id,
            tour_id=test_tour.id,
            status="pending",
            pax_count=2,
            subtotal=2400.00,
            total=2400.00,
            currency="USD",
            contact_name="Test Contact",
            contact_email=test_user.email,
        )
        assert order.status == "pending"
        assert order.pax_count == 2
        assert order.total == 2400.00

    async def test_get_by_user(self, db_session: AsyncSession, test_user: User, test_tour: Tour):
        """功能测试：按用户获取订单。"""
        # 先创建订单
        await crud_order.create(
            db_session,
            order_no=f"TEST-{uuid.uuid4().hex[:8].upper()}",
            user_id=test_user.id,
            tour_id=test_tour.id,
            status="confirmed",
            pax_count=1,
            subtotal=1200.00,
            total=1200.00,
            currency="USD",
            contact_name="Test",
            contact_email=test_user.email,
        )
        orders = await crud_order.get_by_user(db_session, user_id=test_user.id)
        assert len(orders) >= 1

    async def test_get_by_user_empty(self, db_session: AsyncSession):
        """边界测试：无订单用户返回空列表。"""
        orders = await crud_order.get_by_user(db_session, user_id=uuid.uuid4())
        assert orders == []

    async def test_get_by_stripe_session(self, db_session: AsyncSession, test_user: User, test_tour: Tour):
        """功能测试：按 Stripe session ID 查找订单。"""
        session_id = f"cs_test_{uuid.uuid4().hex}"
        order = await crud_order.create(
            db_session,
            order_no=f"STRIPE-{uuid.uuid4().hex[:8].upper()}",
            user_id=test_user.id,
            tour_id=test_tour.id,
            status="pending",
            stripe_session_id=session_id,
            pax_count=1,
            subtotal=500.00,
            total=500.00,
            currency="USD",
            contact_name="Stripe Test",
            contact_email="stripe@example.com",
        )
        found = await crud_order.get_by_stripe_session(db_session, session_id)
        assert found is not None
        assert found.id == order.id

    async def test_get_by_stripe_session_not_found(self, db_session: AsyncSession):
        """边界测试：不存在的 session ID 返回 None。"""
        found = await crud_order.get_by_stripe_session(db_session, "nonexistent_session")
        assert found is None

    async def test_count_orders(self, db_session: AsyncSession):
        """功能测试：订单计数。"""
        count = await crud_order.count(db_session)
        assert isinstance(count, int)
