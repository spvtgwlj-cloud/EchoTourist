"""Wishlist CRUD 层测试。"""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.wishlist import crud_wishlist
from app.models.wishlist import Wishlist


class TestWishlistCRUD:

    async def test_add_wishlist(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：添加收藏。"""
        item = await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=test_tour.id)
        assert item is not None
        assert item.user_id == test_user.id
        assert item.tour_id == test_tour.id

    async def test_add_duplicate_returns_existing(self, db_session: AsyncSession, test_user, test_tour):
        """边界测试：重复添加返回已存在的记录（不抛异常）。"""
        await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=test_tour.id)
        item2 = await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=test_tour.id)
        assert item2 is not None  # 返回已存在的记录
        assert item2.user_id == test_user.id
        assert item2.tour_id == test_tour.id

    async def test_remove_wishlist(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：移除收藏。"""
        await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=test_tour.id)
        removed = await crud_wishlist.remove(db_session, user_id=test_user.id, tour_id=test_tour.id)
        assert removed is True
        is_wl = await crud_wishlist.is_wishlisted(db_session, user_id=test_user.id, tour_id=test_tour.id)
        assert is_wl is False

    async def test_remove_nonexistent(self, db_session: AsyncSession, test_user, test_tour):
        """边界测试：移除不存在的收藏返回 False。"""
        removed = await crud_wishlist.remove(db_session, user_id=test_user.id, tour_id=test_tour.id)
        assert removed is False

    async def test_get_user_wishlist(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：获取用户收藏列表。"""
        from app.models.tour import Tour
        tour2 = Tour(
            id=uuid.uuid4(), slug=f"wish-tour2-{uuid.uuid4().hex[:6]}",
            status="published", type="group_tour",
            duration_days=1, duration_nights=0, start_price=100,
        )
        db_session.add(tour2)
        await db_session.flush()
        await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=test_tour.id)
        await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=tour2.id)
        items = await crud_wishlist.get_user_wishlist(db_session, user_id=test_user.id)
        assert len(items) >= 2

    async def test_get_user_wishlist_empty(self, db_session: AsyncSession, test_user):
        """边界测试：空收藏列表。"""
        items = await crud_wishlist.get_user_wishlist(db_session, user_id=test_user.id)
        assert items == []

    async def test_is_wishlisted(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：检查是否已收藏。"""
        assert await crud_wishlist.is_wishlisted(db_session, user_id=test_user.id, tour_id=test_tour.id) is False
        await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=test_tour.id)
        assert await crud_wishlist.is_wishlisted(db_session, user_id=test_user.id, tour_id=test_tour.id) is True

    async def test_cross_user_wishlists(self, db_session: AsyncSession, test_user, test_tour):
        """功能测试：不同用户收藏互不干扰。"""
        from app.models.user import User
        from app.core.security import hash_password
        user2 = User(
            id=uuid.uuid4(), email=f"user2_{uuid.uuid4().hex[:8]}@example.com",
            name="User Two", hashed_password=hash_password("pass123"), is_active=True,
        )
        db_session.add(user2)
        await db_session.flush()
        await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=test_tour.id)
        await crud_wishlist.add(db_session, user_id=user2.id, tour_id=test_tour.id)
        assert len(await crud_wishlist.get_user_wishlist(db_session, user_id=test_user.id)) >= 1
        assert len(await crud_wishlist.get_user_wishlist(db_session, user_id=user2.id)) >= 1

    async def test_add_invalid_tour(self, db_session: AsyncSession, test_user):
        """鲁棒性测试：为不存在的 tour 添加收藏应抛异常。"""
        from app.core.exceptions import NotFoundException
        with pytest.raises(NotFoundException):
            await crud_wishlist.add(db_session, user_id=test_user.id, tour_id=uuid.uuid4())
