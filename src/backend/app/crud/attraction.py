"""Attraction 景点数据访问操作。"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.attraction import Attraction
from app.models.attraction_ticket import AttractionTicket
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
            .options(selectinload(Attraction.tickets))
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
                "ticket_price": attr.ticket_price or 0,
                "ticket_currency": attr.ticket_currency or "USD",
                "tickets": [
                    {
                        "id": t.id,
                        "attraction_id": t.attraction_id,
                        "ticket_type": t.ticket_type,
                        "price": t.price,
                        "currency": t.currency,
                        "availability": t.availability,
                        "status": t.status,
                    }
                    for t in (attr.tickets or [])
                    if t.status == "available"
                ],
            })
        return items

    async def get_by_slug(
        self, db: AsyncSession, slug: str, locale: str = "en"
    ) -> Optional[dict]:
        """按 slug 获取景点详情。"""
        result = await db.execute(
            select(Attraction)
            .options(selectinload(Attraction.tickets))
            .where(Attraction.slug == slug, Attraction.status == "active")
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
            "ticket_price": attr.ticket_price or 0,
            "ticket_currency": attr.ticket_currency or "USD",
            "tickets": [
                {
                    "id": t.id,
                    "attraction_id": t.attraction_id,
                    "ticket_type": t.ticket_type,
                    "price": t.price,
                    "currency": t.currency,
                    "availability": t.availability,
                    "status": t.status,
                }
                for t in (attr.tickets or [])
                if t.status == "available"
            ],
        }

    @staticmethod
    def _pick_translation(translations, locale: str):
        """按 locale 匹配翻译，无匹配则回退到英文，再回退到第一个。"""
        if not translations:
            return None
        fallback_en = None
        for t in translations:
            if t.locale == locale:
                return t
            if t.locale == 'en':
                fallback_en = t
        return fallback_en or translations[0]


crud_attraction = CRUDAttraction()
