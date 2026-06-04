"""Service 层测试 —— Order。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.order_service import order_service
from app.core.exceptions import NotFoundException, InsufficientStockException
from app.models.tour import Tour, TourDate
from app.models.user import User
from app.schemas.order import BookingRequest


class TestOrderService:
    """Order Service 业务逻辑测试。"""

    async def test_create_booking_success(
        self, db_session: AsyncSession, test_user: User, test_tour: Tour
    ):
        """功能测试：成功创建预订。"""
        # 找到可预订的日期
        from sqlalchemy import select
        result = await db_session.execute(
            select(TourDate).where(
                TourDate.tour_id == test_tour.id,
                TourDate.status == "available",
            ).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()

        req = BookingRequest(
            tour_id=test_tour.id,
            tour_date_id=tour_date.id,
            pax_count=2,
            contact_name="Booking Tester",
            contact_email=test_user.email,
            contact_phone="+1234567890",
            special_requests="Window seat please",
            locale="en",
        )

        order = await order_service.create_booking(db_session, req=req, user=test_user)
        assert order is not None
        assert order.order_no.startswith("ECHO-")
        assert order.pax_count == 2
        assert order.status == "pending"
        assert order.total > 0
        assert order.payment_status == "pending"

    async def test_create_booking_tour_not_found(
        self, db_session: AsyncSession, test_user: User, test_tour: Tour
    ):
        """鲁棒性测试：不存在的产品抛出 404。"""
        from sqlalchemy import select
        result = await db_session.execute(
            select(TourDate).where(
                TourDate.tour_id == test_tour.id,
                TourDate.status == "available",
            ).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()

        req = BookingRequest(
            tour_id=uuid.uuid4(),
            tour_date_id=tour_date.id,
            pax_count=1,
            contact_name="Test",
            contact_email="test@example.com",
            locale="en",
        )
        with pytest.raises(NotFoundException):
            await order_service.create_booking(db_session, req=req, user=test_user)

    async def test_create_booking_date_not_found(
        self, db_session: AsyncSession, test_user: User, test_tour: Tour
    ):
        """鲁棒性测试：不存在的日期抛出 404。"""
        req = BookingRequest(
            tour_id=test_tour.id,
            tour_date_id=uuid.uuid4(),
            pax_count=1,
            contact_name="Test",
            contact_email="test@example.com",
            locale="en",
        )
        with pytest.raises(NotFoundException):
            await order_service.create_booking(db_session, req=req, user=test_user)

    async def test_create_booking_insufficient_stock(
        self, db_session: AsyncSession, test_user: User, test_tour: Tour
    ):
        """鲁棒性测试：库存不足抛出 InsufficientStockException。"""
        from sqlalchemy import select
        result = await db_session.execute(
            select(TourDate).where(
                TourDate.tour_id == test_tour.id,
                TourDate.status == "available",
            ).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()

        # 请求超出库存
        req = BookingRequest(
            tour_id=test_tour.id,
            tour_date_id=tour_date.id,
            pax_count=999,
            contact_name="Overbooking",
            contact_email="over@example.com",
            locale="en",
        )
        with pytest.raises(InsufficientStockException):
            await order_service.create_booking(db_session, req=req, user=test_user)

    async def test_create_booking_updates_availability(
        self, db_session: AsyncSession, test_user: User, test_tour: Tour
    ):
        """功能测试：创建预订后库存减少。"""
        from sqlalchemy import select
        result = await db_session.execute(
            select(TourDate).where(
                TourDate.tour_id == test_tour.id,
                TourDate.status == "available",
            ).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()
        orig_avail = tour_date.availability

        req = BookingRequest(
            tour_id=test_tour.id,
            tour_date_id=tour_date.id,
            pax_count=3,
            contact_name="Availability Test",
            contact_email="avail@example.com",
            locale="en",
        )
        await order_service.create_booking(db_session, req=req, user=test_user)

        # 验证库存减少
        await db_session.refresh(tour_date)
        assert tour_date.availability == orig_avail - 3

    async def test_list_user_orders_empty(
        self, db_session: AsyncSession, test_user: User
    ):
        """功能测试：空订单返回空列表。"""
        # 创建一个全新的用户（没有订单）
        from app.models.user import User
        from app.core.security import hash_password
        new_user = User(
            id=uuid.uuid4(),
            email=f"empty_{uuid.uuid4().hex[:8]}@example.com",
            name="Empty User",
            hashed_password=hash_password("testpass"),
            is_active=True,
        )
        db_session.add(new_user)
        await db_session.flush()

        result = await order_service.list_user_orders(db_session, new_user)
        assert result.orders == []

    async def test_list_user_orders_with_data(
        self, db_session: AsyncSession, test_user: User, test_tour: Tour
    ):
        """功能测试：有订单时返回正确数据。"""
        # 先创建一个订单
        from sqlalchemy import select
        result = await db_session.execute(
            select(TourDate).where(
                TourDate.tour_id == test_tour.id,
                TourDate.status == "available",
            ).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()

        req = BookingRequest(
            tour_id=test_tour.id,
            tour_date_id=tour_date.id,
            pax_count=1,
            contact_name="List Test",
            contact_email=test_user.email,
            locale="en",
        )
        await order_service.create_booking(db_session, req=req, user=test_user)

        result = await order_service.list_user_orders(db_session, test_user)
        assert len(result.orders) >= 1
        assert any(o.contact_name == "List Test" for o in result.orders)

    async def test_get_order_ownership(
        self, db_session: AsyncSession, test_user: User, test_tour: Tour
    ):
        """鲁棒性测试：不能查看其他用户的订单。"""
        from sqlalchemy import select
        from app.core.security import hash_password

        result = await db_session.execute(
            select(TourDate).where(
                TourDate.tour_id == test_tour.id,
                TourDate.status == "available",
            ).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()

        req = BookingRequest(
            tour_id=test_tour.id,
            tour_date_id=tour_date.id,
            pax_count=1,
            contact_name="Owner Test",
            contact_email=test_user.email,
            locale="en",
        )
        order = await order_service.create_booking(db_session, req=req, user=test_user)

        # 另一个用户尝试查看
        other_user = User(
            id=uuid.uuid4(),
            email=f"other_{uuid.uuid4().hex[:8]}@example.com",
            name="Other User",
            hashed_password=hash_password("testpass"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        with pytest.raises(NotFoundException):
            await order_service.get_order(db_session, order.id, other_user)

    async def test_order_number_format(self, db_session: AsyncSession, test_user: User, test_tour: Tour):
        """功能测试：订单号格式正确。"""
        from sqlalchemy import select
        result = await db_session.execute(
            select(TourDate).where(
                TourDate.tour_id == test_tour.id,
                TourDate.status == "available",
            ).order_by(TourDate.start_date)
        )
        tour_date = result.scalars().first()

        req = BookingRequest(
            tour_id=test_tour.id,
            tour_date_id=tour_date.id,
            pax_count=1,
            contact_name="Format Test",
            contact_email="format@example.com",
            locale="en",
        )
        order = await order_service.create_booking(db_session, req=req, user=test_user)

        assert order.order_no.startswith("ECHO-")
        parts = order.order_no.split("-")
        assert len(parts) == 3  # ECHO-YYYYMMDD-XXXXXXXX
        assert len(parts[2]) == 8  # UUID hex prefix
