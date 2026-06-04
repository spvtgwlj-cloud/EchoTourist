"""Wishlist CRUD 操作。"""

import uuid
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.wishlist import Wishlist
from app.models.tour import Tour, TourImage, TourTranslation


class CRUDWishlist(CRUDBase[Wishlist]):
    def __init__(self):
        super().__init__(Wishlist)

    async def add(
        self, db: AsyncSession, user_id: uuid.UUID, tour_id: uuid.UUID
    ) -> Wishlist:
        # Check tour exists
        tour_result = await db.execute(
            select(Tour).where(Tour.id == tour_id, Tour.deleted_at.is_(None))
        )
        if not tour_result.scalar_one_or_none():
            from app.core.exceptions import NotFoundException
            raise NotFoundException(detail="Tour not found")

        # Check existing
        result = await db.execute(
            select(Wishlist).where(
                Wishlist.user_id == user_id,
                Wishlist.tour_id == tour_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        wl = Wishlist(user_id=user_id, tour_id=tour_id)
        db.add(wl)
        await db.flush()
        return wl

    async def remove(
        self, db: AsyncSession, user_id: uuid.UUID, tour_id: uuid.UUID
    ) -> bool:
        result = await db.execute(
            delete(Wishlist).where(
                Wishlist.user_id == user_id,
                Wishlist.tour_id == tour_id,
            )
        )
        await db.flush()
        return result.rowcount > 0

    async def get_user_wishlist(
        self, db: AsyncSession, user_id: uuid.UUID, locale: str = "en"
    ) -> list[dict]:
        result = await db.execute(
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .order_by(Wishlist.created_at.desc())
        )
        wishlist_items = result.scalars().all()

        items = []
        for wl in wishlist_items:
            tour = await db.execute(
                select(Tour)
                .options(
                    selectinload(Tour.tour_images),
                    selectinload(Tour.tour_translations),
                )
                .where(Tour.id == wl.tour_id, Tour.deleted_at.is_(None))
            )
            tour = tour.scalar_one_or_none()
            if not tour:
                continue

            translation = None
            for t in (tour.tour_translations or []):
                if t.locale == locale:
                    translation = t
                    break
            if not translation and tour.tour_translations:
                translation = tour.tour_translations[0]

            image = (tour.tour_images or [None])[0]

            items.append({
                "id": wl.id,
                "tour_id": wl.tour_id,
                "tour_name": translation.name if translation else tour.slug,
                "tour_slug": tour.slug,
                "tour_image": image.url if image else None,
                "start_price": tour.start_price or 0,
                "currency": tour.currency or "USD",
                "avg_rating": tour.avg_rating or 0,
                "created_at": wl.created_at.isoformat() if wl.created_at else "",
            })

        return items

    async def is_wishlisted(
        self, db: AsyncSession, user_id: uuid.UUID, tour_id: uuid.UUID
    ) -> bool:
        result = await db.execute(
            select(func.count(Wishlist.id)).where(
                Wishlist.user_id == user_id,
                Wishlist.tour_id == tour_id,
            )
        )
        return result.scalar() > 0


crud_wishlist = CRUDWishlist()
