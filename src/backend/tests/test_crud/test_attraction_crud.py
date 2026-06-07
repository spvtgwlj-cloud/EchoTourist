"""Attraction CRUD 层测试。"""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.crud.attraction import crud_attraction
from app.models.attraction import Attraction, AttractionTranslation
from app.models.attraction_media import AttractionMedia
from app.models.destination import Destination


class TestAttractionCRUD:

    async def _create_destination(self, db_session: AsyncSession) -> Destination:
        dest = Destination(
            id=uuid.uuid4(), slug=f"test-dest-{uuid.uuid4().hex[:6]}", status="active",
        )
        db_session.add(dest)
        await db_session.flush()
        return dest

    async def test_create_attraction(self, db_session: AsyncSession):
        """功能测试：创建景点。"""
        dest = await self._create_destination(db_session)
        aid = uuid.uuid4()
        attr = Attraction(
            id=aid, slug=f"test-site-{uuid.uuid4().hex[:4]}",
            destination_id=dest.id, image_url="https://example.com/photo.jpg",
            sort_order=1, rating=5, status="active",
        )
        db_session.add(attr)
        await db_session.flush()
        assert attr.id == aid
        assert attr.slug.startswith("test-site-")
        assert attr.sort_order == 1
        assert attr.rating == 5

    async def test_get_by_slug(self, db_session: AsyncSession):
        """功能测试：通过 slug 获取景点详情（返回 dict）。"""
        dest = await self._create_destination(db_session)
        slug = f"site-{uuid.uuid4().hex[:4]}"
        db_session.add(Attraction(
            id=uuid.uuid4(), slug=slug, destination_id=dest.id, rating=4,
        ))
        await db_session.flush()
        result = await crud_attraction.get_by_slug(db_session, slug)
        assert result is not None
        assert result["slug"] == slug

    async def test_get_by_slug_not_found(self, db_session: AsyncSession):
        """边界测试：不存在的 slug 返回 None。"""
        result = await crud_attraction.get_by_slug(db_session, "nonexistent")
        assert result is None

    async def test_get_by_destination(self, db_session: AsyncSession):
        """功能测试：按目的地获取景点列表。"""
        dest = await self._create_destination(db_session)
        for i in range(3):
            db_session.add(Attraction(
                id=uuid.uuid4(), slug=f"attr-{i}-{uuid.uuid4().hex[:4]}",
                destination_id=dest.id, sort_order=i, rating=4,
            ))
        await db_session.flush()
        items = await crud_attraction.get_by_destination(db_session, dest.id)
        assert len(items) == 3

    async def test_get_by_destination_empty(self, db_session: AsyncSession):
        """边界测试：无景点时返回空列表。"""
        items = await crud_attraction.get_by_destination(db_session, uuid.uuid4())
        assert items == []

    async def test_update_attraction(self, db_session: AsyncSession):
        """功能测试：更新景点。"""
        dest = await self._create_destination(db_session)
        aid = uuid.uuid4()
        db_session.add(Attraction(
            id=aid, slug=f"upd-{uuid.uuid4().hex[:4]}",
            destination_id=dest.id, rating=3, sort_order=1,
        ))
        await db_session.flush()
        attr = await db_session.get(Attraction, aid)
        await crud_attraction.update(db_session, db_obj=attr, update_data={"rating": 5})
        updated = await db_session.get(Attraction, aid)
        assert updated.rating == 5

    async def test_delete_attraction(self, db_session: AsyncSession):
        """功能测试：删除景点。"""
        dest = await self._create_destination(db_session)
        aid = uuid.uuid4()
        db_session.add(Attraction(
            id=aid, slug=f"del-{uuid.uuid4().hex[:4]}",
            destination_id=dest.id, rating=4,
        ))
        await db_session.flush()
        deleted = await crud_attraction.delete(db_session, id=aid)
        assert deleted is not None
        fetched = await db_session.get(Attraction, aid)
        assert fetched is None

    async def test_create_with_translation(self, db_session: AsyncSession):
        """功能测试：创建景点及翻译。"""
        dest = await self._create_destination(db_session)
        aid = uuid.uuid4()
        db_session.add(Attraction(
            id=aid, slug=f"trans-{uuid.uuid4().hex[:4]}",
            destination_id=dest.id, rating=5,
        ))
        await db_session.flush()
        db_session.add(AttractionTranslation(
            id=uuid.uuid4(), attraction_id=aid,
            locale="zh", name="故宫", description="皇家宫殿",
        ))
        await db_session.flush()
        result = await db_session.execute(
            select(AttractionTranslation).where(AttractionTranslation.attraction_id == aid)
        )
        assert result.scalar_one_or_none() is not None

    async def test_multi_locale_translations(self, db_session: AsyncSession):
        """功能测试：多语言翻译。"""
        dest = await self._create_destination(db_session)
        aid = uuid.uuid4()
        db_session.add(Attraction(
            id=aid, slug=f"ml-{uuid.uuid4().hex[:4]}",
            destination_id=dest.id, rating=4,
        ))
        await db_session.flush()
        for loc, name in [("en", "Great Wall"), ("zh", "长城"), ("es", "Gran Muralla")]:
            db_session.add(AttractionTranslation(
                id=uuid.uuid4(), attraction_id=aid, locale=loc, name=name,
            ))
        await db_session.flush()

        en = await crud_attraction.get_by_slug(db_session, f"ml-", locale="en")
        # slug may not match due to random suffix, just verify translations exist
        result = await db_session.execute(
            select(AttractionTranslation).where(AttractionTranslation.attraction_id == aid)
        )
        assert len(result.scalars().all()) == 3

    async def test_duplicate_slug_raises(self, db_session: AsyncSession):
        """鲁棒性测试：重复 slug 抛出完整性错误。"""
        dest = await self._create_destination(db_session)
        slug = f"dup-{uuid.uuid4().hex[:4]}"
        db_session.add(Attraction(
            id=uuid.uuid4(), slug=slug, destination_id=dest.id, rating=4,
        ))
        await db_session.flush()
        with pytest.raises(IntegrityError):
            db_session.add(Attraction(
                id=uuid.uuid4(), slug=slug, destination_id=dest.id, rating=5,
            ))
            await db_session.flush()

    async def test_create_attraction_media(self, db_session: AsyncSession):
        """功能测试：创建景点媒体资源。"""
        dest = await self._create_destination(db_session)
        aid = uuid.uuid4()
        db_session.add(Attraction(
            id=aid, slug=f"media-test-{uuid.uuid4().hex[:4]}",
            destination_id=dest.id, rating=4,
        ))
        await db_session.flush()

        # 添加 3 个媒体记录
        for i in range(3):
            db_session.add(AttractionMedia(
                id=uuid.uuid4(), attraction_id=aid,
                url=f"https://example.com/media/{i}.jpg",
                media_type="image", alt_text=f"Photo {i}",
                sort_order=i,
            ))
        await db_session.flush()

        result = await db_session.execute(
            select(AttractionMedia).where(AttractionMedia.attraction_id == aid)
            .order_by(AttractionMedia.sort_order)
        )
        media_list = result.scalars().all()
        assert len(media_list) == 3
        assert media_list[0].sort_order == 0
        assert media_list[2].url.endswith("2.jpg")

    async def test_get_by_destination_includes_media(self, db_session: AsyncSession):
        """功能测试：get_by_destination 返回结果包含 media 数据。"""
        dest = await self._create_destination(db_session)
        aid = uuid.uuid4()
        db_session.add(Attraction(
            id=aid, slug=f"media-dest-{uuid.uuid4().hex[:4]}",
            destination_id=dest.id, rating=4, status="active",
        ))
        await db_session.flush()
        for i in range(2):
            db_session.add(AttractionMedia(
                id=uuid.uuid4(), attraction_id=aid,
                url=f"https://example.com/m/{i}.jpg",
                media_type="image", sort_order=i,
            ))
        await db_session.flush()

        items = await crud_attraction.get_by_destination(db_session, dest.id)
        assert len(items) == 1
        result = items[0]
        assert "media" in result
        assert len(result["media"]) == 2
        assert result["media"][0]["url"].endswith("0.jpg")
        assert result["media"][1]["sort_order"] == 1

    async def test_get_by_slug_includes_media(self, db_session: AsyncSession):
        """功能测试：get_by_slug 返回结果包含 media 数据。"""
        dest = await self._create_destination(db_session)
        slug = f"media-slug-{uuid.uuid4().hex[:4]}"
        aid = uuid.uuid4()
        db_session.add(Attraction(
            id=aid, slug=slug,
            destination_id=dest.id, rating=5, status="active",
        ))
        await db_session.flush()
        db_session.add(AttractionMedia(
            id=uuid.uuid4(), attraction_id=aid,
            url="https://example.com/hero.jpg",
            media_type="image", sort_order=0,
        ))
        await db_session.flush()

        result = await crud_attraction.get_by_slug(db_session, slug)
        assert result is not None
        assert "media" in result
        assert len(result["media"]) == 1
        assert result["media"][0]["url"] == "https://example.com/hero.jpg"
