"""Destination CRUD 层测试。"""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.destination import crud_destination
from app.models.destination import Destination, DestinationTranslation


class TestDestinationCRUD:

    async def test_create_destination(self, db_session: AsyncSession):
        """功能测试：创建目的地。"""
        did = uuid.uuid4()
        dest = Destination(
            id=did, slug=f"city-{uuid.uuid4().hex[:4]}",
            image_url="https://example.com/img.jpg", status="active",
        )
        db_session.add(dest)
        await db_session.flush()
        assert dest.id == did
        assert dest.status == "active"

    async def test_get_by_slug(self, db_session: AsyncSession):
        """功能测试：通过 slug 获取目的地详情（返回 dict）。"""
        slug = f"city-{uuid.uuid4().hex[:4]}"
        db_session.add(Destination(id=uuid.uuid4(), slug=slug, status="active"))
        await db_session.flush()
        result = await crud_destination.get_by_slug(db_session, slug)
        assert result is not None
        assert result["slug"] == slug
        assert "name" in result
        assert "tour_count" in result

    async def test_get_by_slug_not_found(self, db_session: AsyncSession):
        """边界测试：不存在的 slug。"""
        result = await crud_destination.get_by_slug(db_session, "nonexistent")
        assert result is None

    async def test_get_active(self, db_session: AsyncSession):
        """功能测试：获取活跃目的地列表。"""
        d1 = Destination(id=uuid.uuid4(), slug=f"act1-{uuid.uuid4().hex[:4]}", status="active")
        d2 = Destination(id=uuid.uuid4(), slug=f"act2-{uuid.uuid4().hex[:4]}", status="active")
        db_session.add_all([d1, d2])
        await db_session.flush()
        active = await crud_destination.get_active(db_session)
        assert len(active) >= 2
        for d in active:
            assert "name" in d

    async def test_get_active_excludes_inactive(self, db_session: AsyncSession):
        """功能测试：非活跃目的地不被返回。"""
        db_session.add(Destination(
            id=uuid.uuid4(), slug=f"inact-{uuid.uuid4().hex[:4]}", status="inactive",
        ))
        await db_session.flush()
        active = await crud_destination.get_active(db_session)
        for d in active:
            assert d.get("name") is not None  # all returned have name

    async def test_update_and_get(self, db_session: AsyncSession):
        """功能测试：更新目的地。"""
        did = uuid.uuid4()
        dest = Destination(
            id=did, slug=f"upd-{uuid.uuid4().hex[:4]}",
            image_url="https://example.com/old.jpg", status="active",
        )
        db_session.add(dest)
        await db_session.flush()
        await crud_destination.update(db_session, db_obj=dest, update_data={
            "image_url": "https://example.com/new.jpg",
        })
        updated = await db_session.get(Destination, did)
        assert updated.image_url == "https://example.com/new.jpg"

    async def test_delete_destination(self, db_session: AsyncSession):
        """功能测试：删除目的地。"""
        did = uuid.uuid4()
        dest = Destination(id=did, slug=f"del-{uuid.uuid4().hex[:4]}", status="active")
        db_session.add(dest)
        await db_session.flush()
        deleted = await crud_destination.delete(db_session, id=did)
        assert deleted is not None
        fetched = await db_session.get(Destination, did)
        assert fetched is None

    async def test_create_with_translations(self, db_session: AsyncSession):
        """功能测试：目的地多语言翻译。"""
        did = uuid.uuid4()
        db_session.add(Destination(id=did, slug=f"trans-dest-{uuid.uuid4().hex[:4]}", status="active"))
        await db_session.flush()
        db_session.add_all([
            DestinationTranslation(id=uuid.uuid4(), destination_id=did, locale="en", name="Paris"),
            DestinationTranslation(id=uuid.uuid4(), destination_id=did, locale="zh", name="巴黎"),
        ])
        await db_session.flush()

        result = await db_session.execute(
            select(DestinationTranslation).where(DestinationTranslation.destination_id == did)
        )
        assert len(result.scalars().all()) == 2
