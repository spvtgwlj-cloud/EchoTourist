"""Attraction 景点数据访问操作。"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.attraction import Attraction
from app.models.destination import Destination


class CRUDAttraction(CRUDBase[Attraction]):
    def __init__(self):
        super().__init__(Attraction)

    async def get_by_destination(
        self, db: AsyncSession, destination_id: UUID, locale: str = "en"
    ) -> list[dict]:
        """获取指定目的地下的所有活跃景点，按 sort_order 排序。"""
        result = await db.execute(
            select(Attraction)
            .where(Attraction.destination_id == destination_id, Attraction.status == "active")
            .order_by(Attraction.sort_order)
        )
        attractions = result.scalars().all()

        items = []
        for attr in attractions:
            translation = self._pick_translation(attr.translations, locale)
            items.append({
                "id": attr.id,
                "slug": attr.slug,
                "destination_id": attr.destination_id,
                "name": translation.name if translation else attr.slug,
                "description": translation.description if translation else None,
                "image_url": attr.image_url,
                "sort_order": attr.sort_order or 0,
                "rating": attr.rating or 0,
            })
        return items

    async def get_by_slug(
        self, db: AsyncSession, slug: str, locale: str = "en"
    ) -> Optional[dict]:
        """按 slug 获取景点详情。"""
        result = await db.execute(
            select(Attraction).where(Attraction.slug == slug, Attraction.status == "active")
        )
        attr = result.scalar_one_or_none()
        if not attr:
            return None

        translation = self._pick_translation(attr.translations, locale)
        return {
            "id": attr.id,
            "slug": attr.slug,
            "destination_id": attr.destination_id,
            "name": translation.name if translation else attr.slug,
            "description": translation.description if translation else None,
            "image_url": attr.image_url,
            "sort_order": attr.sort_order or 0,
            "rating": attr.rating or 0,
        }

    @staticmethod
    def _pick_translation(translations, locale: str):
        """按 locale 匹配翻译，无匹配则回退到第一个。"""
        if not translations:
            return None
        for t in translations:
            if t.locale == locale:
                return t
        return translations[0]


crud_attraction = CRUDAttraction()
