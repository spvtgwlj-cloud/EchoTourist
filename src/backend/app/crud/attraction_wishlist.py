"""AttractionWishlist 景点收藏 CRUD 操作。"""

import uuid

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.attraction_wishlist import AttractionWishlist
from app.models.attraction import Attraction


class CRUDAttractionWishlist(CRUDBase[AttractionWishlist]):
    def __init__(self):
        super().__init__(AttractionWishlist)

    async def add(
        self, db: AsyncSession, user_id: uuid.UUID, attraction_id: uuid.UUID
    ) -> AttractionWishlist:
        # Check attraction exists
        attr_result = await db.execute(
            select(Attraction).where(Attraction.id == attraction_id, Attraction.status == "active")
        )
        if not attr_result.scalar_one_or_none():
            from app.core.exceptions import NotFoundException
            raise NotFoundException(detail="Attraction not found")

        # Check existing
        result = await db.execute(
            select(AttractionWishlist).where(
                AttractionWishlist.user_id == user_id,
                AttractionWishlist.attraction_id == attraction_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        wl = AttractionWishlist(user_id=user_id, attraction_id=attraction_id)
        db.add(wl)
        await db.flush()
        return wl

    async def remove(
        self, db: AsyncSession, user_id: uuid.UUID, attraction_id: uuid.UUID
    ) -> bool:
        result = await db.execute(
            delete(AttractionWishlist).where(
                AttractionWishlist.user_id == user_id,
                AttractionWishlist.attraction_id == attraction_id,
            )
        )
        await db.flush()
        return result.rowcount > 0

    async def get_user_wishlist(
        self, db: AsyncSession, user_id: uuid.UUID, locale: str = "en"
    ) -> list[dict]:
        result = await db.execute(
            select(AttractionWishlist)
            .where(AttractionWishlist.user_id == user_id)
            .order_by(AttractionWishlist.created_at.desc())
        )
        wishlist_items = result.scalars().all()

        items = []
        for wl in wishlist_items:
            attr_result = await db.execute(
                select(Attraction).where(Attraction.id == wl.attraction_id, Attraction.status == "active")
            )
            attr = attr_result.scalar_one_or_none()
            if not attr:
                continue

            # Pick translation by locale
            translation = None
            locale_fallback = None
            for t in (attr.translations or []):
                if t.locale == locale:
                    translation = t
                    break
                if t.locale == "en":
                    locale_fallback = t
            if not translation:
                translation = locale_fallback or (attr.translations[0] if attr.translations else None)

            items.append({
                "id": wl.id,
                "attraction_id": wl.attraction_id,
                "attraction_name": translation.name if translation else attr.slug,
                "attraction_slug": attr.slug,
                "attraction_image": attr.image_url,
                "rating": attr.rating or 0,
                "created_at": wl.created_at.isoformat() if wl.created_at else "",
            })

        return items

    async def is_wishlisted(
        self, db: AsyncSession, user_id: uuid.UUID, attraction_id: uuid.UUID
    ) -> bool:
        result = await db.execute(
            select(func.count(AttractionWishlist.id)).where(
                AttractionWishlist.user_id == user_id,
                AttractionWishlist.attraction_id == attraction_id,
            )
        )
        return result.scalar() > 0


crud_attraction_wishlist = CRUDAttractionWishlist()
