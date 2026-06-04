"""Destination CRUD 操作。"""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.crud.base import CRUDBase
from app.models.destination import Destination, DestinationTranslation
from app.models.tour import Tour


class CRUDDestination(CRUDBase[Destination]):
    def __init__(self):
        super().__init__(Destination)

    async def get_active(
        self, db: AsyncSession, locale: str = "en"
    ) -> list[dict]:
        result = await db.execute(
            select(Destination).where(Destination.status == "active")
        )
        destinations = result.scalars().all()

        items = []
        for dest in destinations:
            translation = None
            for t in (dest.translations or []):
                if t.locale == locale:
                    translation = t
                    break
            if not translation and dest.translations:
                translation = dest.translations[0]

            # Count tours for this destination
            if dest.id:
                count_result = await db.execute(
                    select(func.count(Tour.id)).where(
                        Tour.destination_ids.any(dest.id),
                        Tour.status == "published",
                        Tour.deleted_at.is_(None),
                    )
                )
                tour_count = count_result.scalar() or 0
            else:
                tour_count = 0

            items.append({
                "id": dest.id,
                "slug": dest.slug,
                "name": translation.name if translation else dest.slug,
                "description": translation.description if translation else None,
                "image_url": dest.image_url,
                "tour_count": tour_count,
            })

        return items

    async def get_by_slug(
        self, db: AsyncSession, slug: str, locale: str = "en"
    ) -> Optional[dict]:
        result = await db.execute(
            select(Destination).where(
                Destination.slug == slug, Destination.status == "active"
            )
        )
        dest = result.scalar_one_or_none()
        if not dest:
            return None

        translation = None
        for t in (dest.translations or []):
            if t.locale == locale:
                translation = t
                break
        if not translation and dest.translations:
            translation = dest.translations[0]

        count_result = await db.execute(
            select(func.count(Tour.id)).where(
                Tour.destination_ids.any(dest.id),
                Tour.status == "published",
                Tour.deleted_at.is_(None),
            )
        )

        return {
            "id": dest.id,
            "slug": dest.slug,
            "name": translation.name if translation else dest.slug,
            "description": translation.description if translation else None,
            "image_url": dest.image_url,
            "tour_count": count_result.scalar() or 0,
        }


crud_destination = CRUDDestination()
