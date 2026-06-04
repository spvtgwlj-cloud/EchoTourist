"""Review CRUD 层测试。"""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud.review import crud_review
from app.models.review import Review


class TestReviewCRUD:

    async def test_create_review(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：创建评论。"""
        review = await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=5, title="Amazing!", comment="Best experience ever.", locale="en",
        )
        assert review is not None
        assert review.rating == 5
        assert review.title == "Amazing!"
        assert review.status == "approved"  # auto-approve

    async def test_create_review_updates_rating(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：创建评论后自动更新评分。"""
        await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=4, title="Good tour", locale="en",
        )
        await db_session.refresh(test_tour)
        assert test_tour.avg_rating > 0
        assert test_tour.review_count >= 1

    async def test_create_review_nonexistent_tour(self, db_session: AsyncSession, test_user):
        """鲁棒性测试：为不存在的 tour 创建评论抛异常。"""
        with pytest.raises(IntegrityError):
            await crud_review.create_review(
                db_session, tour_id=uuid.uuid4(), user_id=test_user.id,
                rating=3, title="Bad", locale="en",
            )
            await db_session.flush()

    async def test_get_tour_reviews(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：获取产品评论（每个用户只能评论一次）。"""
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

    async def test_get_tour_reviews_with_status_filter(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：按状态筛选评论（默认仅返回 approved）。"""
        await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=5, title="Auto approved", locale="en",
        )
        reviews, total, _ = await crud_review.get_tour_reviews(db_session, test_tour.id, status="approved")
        assert total == 1

    async def test_multi_user_reviews_same_tour(self, db_session: AsyncSession, test_tour):
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
            await crud_review.create_review(
                db_session, tour_id=test_tour.id, user_id=u.id,
                rating=4, title="Nice tour", locale="en",
            )
        await db_session.refresh(test_tour)
        assert test_tour.review_count >= 3

    async def test_rating_boundaries(self, db_session: AsyncSession, test_user, test_tour):
        """边界测试：评分极端值（每个用户只能评论一次）。"""
        from app.models.user import User
        from app.core.security import hash_password
        r1 = await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=test_user.id,
            rating=1, title="Terrible", locale="en",
        )
        assert r1.rating == 1
        # Use a second user for rating=5
        user2 = User(
            id=uuid.uuid4(),
            email=f"r5_{uuid.uuid4().hex[:6]}@example.com",
            name="Rating 5 User",
            hashed_password=hash_password("pass"), is_active=True,
        )
        db_session.add(user2)
        await db_session.flush()
        r5 = await crud_review.create_review(
            db_session, tour_id=test_tour.id, user_id=user2.id,
            rating=5, title="Perfect", locale="en",
        )
        assert r5.rating == 5
