"""AttractionWishlist 景点收藏 CRUD 层测试。

覆盖范围：
- 正常添加景点收藏
- 重复添加返回已有记录
- 移除收藏
- 移除不存在的收藏
- 获取用户收藏列表（含/不含景点）
- 检查是否已收藏
- 不同用户收藏互不干扰
- 收藏已删除/不活跃景点
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.attraction_wishlist import crud_attraction_wishlist
from app.models.attraction import Attraction
from app.models.user import User
from app.core.security import hash_password


class TestAttractionWishlistCRUD:

    async def test_add_wishlist(self, db_session: AsyncSession, test_user, test_attraction):
        """TC-WISH-ATTR-001：正常添加景点收藏。"""
        item = await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        assert item is not None
        assert item.user_id == test_user.id
        assert item.attraction_id == test_attraction.id

    async def test_add_duplicate_returns_existing(
        self, db_session: AsyncSession, test_user, test_attraction,
    ):
        """TC-WISH-ATTR-002：重复添加返回已有记录（不抛异常）。"""
        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        item2 = await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        assert item2 is not None
        assert item2.user_id == test_user.id
        assert item2.attraction_id == test_attraction.id

    async def test_remove_wishlist(self, db_session: AsyncSession, test_user, test_attraction):
        """TC-WISH-ATTR-003：移除景点收藏。"""
        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        removed = await crud_attraction_wishlist.remove(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        assert removed is True
        is_wl = await crud_attraction_wishlist.is_wishlisted(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        assert is_wl is False

    async def test_remove_nonexistent(self, db_session: AsyncSession, test_user, test_attraction):
        """TC-WISH-ATTR-004：移除不存在的收藏返回 False。"""
        removed = await crud_attraction_wishlist.remove(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        assert removed is False

    async def test_get_user_wishlist(self, db_session: AsyncSession, test_user, test_attraction):
        """TC-WISH-ATTR-005：获取用户收藏列表（含多个景点）。"""
        # 创建第二个景点
        from app.models.attraction import Attraction, AttractionTranslation
        attr2 = Attraction(
            id=uuid.uuid4(), slug=f"wish-attr2-{uuid.uuid4().hex[:6]}",
            destination_id=test_attraction.destination_id,
            status="active", rating=3,
        )
        db_session.add(attr2)
        db_session.add(AttractionTranslation(
            id=uuid.uuid4(), attraction_id=attr2.id,
            locale="en", name="Wish Attraction Two",
        ))
        await db_session.flush()

        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=attr2.id,
        )

        items = await crud_attraction_wishlist.get_user_wishlist(
            db_session, user_id=test_user.id,
        )
        assert len(items) >= 2
        names = [i["attraction_name"] for i in items]
        assert "Test Attraction" in names
        assert "Wish Attraction Two" in names

    async def test_get_user_wishlist_empty(self, db_session: AsyncSession, test_user):
        """TC-WISH-ATTR-006：空收藏列表。"""
        items = await crud_attraction_wishlist.get_user_wishlist(
            db_session, user_id=test_user.id,
        )
        assert items == []

    async def test_is_wishlisted(self, db_session: AsyncSession, test_user, test_attraction):
        """TC-WISH-ATTR-007：检查是否已收藏。"""
        assert await crud_attraction_wishlist.is_wishlisted(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        ) is False
        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        assert await crud_attraction_wishlist.is_wishlisted(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        ) is True

    async def test_cross_user_wishlists(self, db_session: AsyncSession, test_user, test_attraction):
        """TC-WISH-ATTR-008：不同用户收藏互不干扰。"""
        user2 = User(
            id=uuid.uuid4(), email=f"user2_{uuid.uuid4().hex[:8]}@example.com",
            name="User Two", hashed_password=hash_password("pass123"), is_active=True,
        )
        db_session.add(user2)
        await db_session.flush()

        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        await crud_attraction_wishlist.add(
            db_session, user_id=user2.id, attraction_id=test_attraction.id,
        )
        assert len(await crud_attraction_wishlist.get_user_wishlist(
            db_session, user_id=test_user.id,
        )) >= 1
        assert len(await crud_attraction_wishlist.get_user_wishlist(
            db_session, user_id=user2.id,
        )) >= 1

    async def test_add_invalid_attraction(self, db_session: AsyncSession, test_user):
        """TC-WISH-ATTR-009：不存在的景点 ID 抛 NotFoundException。"""
        from app.core.exceptions import NotFoundException
        with pytest.raises(NotFoundException):
            await crud_attraction_wishlist.add(
                db_session, user_id=test_user.id, attraction_id=uuid.uuid4(),
            )

    async def test_add_inactive_attraction(self, db_session: AsyncSession, test_user, test_attraction):
        """TC-WISH-ATTR-010：收藏不活跃（非 active）景点抛 NotFoundException。"""
        from app.core.exceptions import NotFoundException
        test_attraction.status = "inactive"
        await db_session.flush()
        with pytest.raises(NotFoundException):
            await crud_attraction_wishlist.add(
                db_session, user_id=test_user.id, attraction_id=test_attraction.id,
            )

    async def test_get_wishlist_skips_deleted_attractions(
        self, db_session: AsyncSession, test_user, test_attraction,
    ):
        """TC-WISH-ATTR-011：收藏列表自动跳过已删除/不活跃的景点。"""
        # 收藏一个景点后将其标记为不活跃
        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        test_attraction.status = "inactive"
        await db_session.flush()

        items = await crud_attraction_wishlist.get_user_wishlist(
            db_session, user_id=test_user.id,
        )
        assert items == []

    async def test_wishlist_respects_locale(
        self, db_session: AsyncSession, test_user, test_attraction,
    ):
        """TC-WISH-ATTR-012：收藏列表返回对应语言的景点名称。"""
        await crud_attraction_wishlist.add(
            db_session, user_id=test_user.id, attraction_id=test_attraction.id,
        )
        items_en = await crud_attraction_wishlist.get_user_wishlist(
            db_session, user_id=test_user.id, locale="en",
        )
        assert items_en[0]["attraction_name"] == "Test Attraction"

        items_zh = await crud_attraction_wishlist.get_user_wishlist(
            db_session, user_id=test_user.id, locale="zh",
        )
        assert items_zh[0]["attraction_name"] == "测试景点"
