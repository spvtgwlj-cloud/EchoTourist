"""Review CRUD 层测试。"""

import uuid
import pytest
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud.review import crud_review
from app.core.exceptions import ValidationException
from app.models.review import Review
from app.models.order import Order
from app.models.tour import TourDate


async def _create_confirmed_order(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID,
    tour_id: uuid.UUID,
    tour_date_id: uuid.UUID,
    order_no_prefix: str = "ORD",
) -> Order:
    """辅助：为测试用户创建已确认订单（满足评价前置条件）。"""
    order = Order(
        id=uuid.uuid4(),
        order_no=f"{order_no_prefix}-{uuid.uuid4().hex[:8].upper()}",
        user_id=user_id,
        tour_id=tour_id,
        tour_date_id=tour_date_id,
        status="confirmed",
        payment_status="paid",
        pax_count=1,
        subtotal=100,
        total=100,
        currency="USD",
        contact_name="Test Reviewer",
        contact_email="test_reviewer@example.com",
    )
    db_session.add(order)
    await db_session.flush()
    return order


class TestReviewCRUD:

    async def test_create_review(self, db_session: AsyncSession, test_user, test_tour, test_tour_date):
        """功能测试：创建评论。"""
        await _create_confirmed_order(
            db_session, user_id=test_user.id, tour_id=test_tour.id, tour_date_id=test_tour_date.id,
        )
        review = await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=5, title="Amazing!", comment="Best experience ever.", locale="en",
        )
        assert review is not None
        assert review.rating == 5
        assert review.title == "Amazing!"
        assert review.status == "approved"  # auto-approve

    async def test_create_review_updates_rating(self, db_session: AsyncSession, test_user, test_tour, test_tour_date):
        """功能测试：创建评论后自动更新评分。"""
        await _create_confirmed_order(
            db_session, user_id=test_user.id, tour_id=test_tour.id, tour_date_id=test_tour_date.id,
        )
        await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=4, title="Good tour", locale="en",
        )
        await db_session.refresh(test_tour)
        assert test_tour.avg_rating > 0
        assert test_tour.review_count >= 1

    async def test_create_review_nonexistent_tour(self, db_session: AsyncSession, test_user):
        """鲁棒性测试：为不存在的 tour 创建评论 — 此时先触发订单检查（ValidationException）。"""
        with pytest.raises(ValidationException):
            await crud_review.create_review(
                db_session, tour_id=uuid.uuid4(), user_id=test_user.id,
                rating=3, title="Bad", locale="en",
            )

    async def test_create_review_without_order_rejected(self, db_session: AsyncSession, test_user, test_tour):
        """TC-REV-005：无已确认订单时评价被拒绝。"""
        with pytest.raises(ValidationException):
            await crud_review.create_review(
                db_session, tour_id=test_tour.id, user_id=test_user.id,
                rating=4, title="No booking", locale="en",
            )

    async def test_get_tour_reviews(self, db_session: AsyncSession, test_user, test_tour, test_tour_date):
        """功能测试：获取产品评论。"""
        from app.models.user import User
        from app.core.security import hash_password
        users = []
        for i in range(3):
            u = User(
                id=uuid.uuid4(),
                email=f"grv{i}_{uuid.uuid4().hex[:6]}@example.com",
                name=f"GetReviewer {i}",
                hashed_password=hash_password("pass"), is_active=True,
            )
            db_session.add(u)
            users.append(u)
        await db_session.flush()
        for i, u in enumerate(users):
            await _create_confirmed_order(
                db_session, user_id=u.id, tour_id=test_tour.id,
                tour_date_id=test_tour_date.id, order_no_prefix=f"GRV{i}",
            )
            await crud_review.create_review(
                db_session, tour_id=test_tour.id, user_id=u.id,
                rating=4 + i % 2, title=f"Review {i}", locale="en",
            )
        reviews, total, avg = await crud_review.get_tour_reviews(db_session, test_tour.id)
        assert total == 3
        assert avg > 0

    async def test_get_tour_reviews_empty(self, db_session: AsyncSession, test_tour):
        """边界测试：无评论。"""
        reviews, total, avg = await crud_review.get_tour_reviews(db_session, test_tour.id)
        assert total == 0
        assert avg == 0.0

    async def test_get_tour_reviews_invalid_id(self, db_session: AsyncSession):
        """边界测试：无效产品 ID。"""
        reviews, total, avg = await crud_review.get_tour_reviews(db_session, uuid.uuid4())
        assert total == 0

    async def test_get_tour_reviews_with_status_filter(self, db_session: AsyncSession, test_user, test_tour, test_tour_date):
        """功能测试：按状态筛选评论（默认仅返回 approved）。"""
        await _create_confirmed_order(
            db_session, user_id=test_user.id, tour_id=test_tour.id, tour_date_id=test_tour_date.id,
        )
        await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=5, title="Auto approved", locale="en",
        )
        reviews, total, _ = await crud_review.get_tour_reviews(db_session, test_tour.id, status="approved")
        assert total == 1

    async def test_multi_user_reviews_same_tour(self, db_session: AsyncSession, test_tour, test_tour_date):
        """功能测试：多用户评论同一产品。"""
        from app.models.user import User
        from app.core.security import hash_password
        users = []
        for i in range(3):
            u = User(
                id=uuid.uuid4(),
                email=f"rv{i}_{uuid.uuid4().hex[:6]}@example.com",
                name=f"Reviewer {i}",
                hashed_password=hash_password("pass"), is_active=True,
            )
            db_session.add(u)
            users.append(u)
        await db_session.flush()
        for u in users:
            await _create_confirmed_order(
                db_session, user_id=u.id, tour_id=test_tour.id,
                tour_date_id=test_tour_date.id, order_no_prefix="MUR",
            )
            await crud_review.create_review(
                db_session, tour_id=test_tour.id, user_id=u.id,
                rating=4, title="Nice tour", locale="en",
            )
        await db_session.refresh(test_tour)
        assert test_tour.review_count >= 3

    async def test_rating_boundaries(self, db_session: AsyncSession, test_user, test_tour, test_tour_date):
        """边界测试：评分极端值。"""
        from app.models.user import User
        from app.core.security import hash_password
        # User 1: rating=1
        await _create_confirmed_order(
            db_session, user_id=test_user.id, tour_id=test_tour.id, tour_date_id=test_tour_date.id,
        )
        r1 = await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=1, title="Terrible", locale="en",
        )
        assert r1.rating == 1
        # User 2: rating=5
        user2 = User(
            id=uuid.uuid4(),
            email=f"r5_{uuid.uuid4().hex[:6]}@example.com",
            name="Rating 5 User",
            hashed_password=hash_password("pass"), is_active=True,
        )
        db_session.add(user2)
        await db_session.flush()
        await _create_confirmed_order(
            db_session, user_id=user2.id, tour_id=test_tour.id,
            tour_date_id=test_tour_date.id, order_no_prefix="RB5",
        )
        r5 = await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=user2.id,
            rating=5, title="Perfect", locale="en",
        )
        assert r5.rating == 5
