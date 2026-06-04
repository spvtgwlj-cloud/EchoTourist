"""Tour 相关数据访问操作。"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.tour import Tour, TourTranslation, TourDate, TourImage


class CRUDTour(CRUDBase[Tour]):
    def __init__(self):
        super().__init__(Tour)

    async def get_with_details(self, db: AsyncSession, tour_id: UUID, locale: str) -> Optional[Tour]:
        query = (
            select(Tour)
            .options(
                selectinload(Tour.tour_translations),
                selectinload(Tour.tour_images),
                selectinload(Tour.tour_dates),
            )
            .where(Tour.id == tour_id, Tour.deleted_at.is_(None))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, db: AsyncSession, slug: str, locale: str) -> Optional[Tour]:
        query = (
            select(Tour)
            .options(
                selectinload(Tour.tour_translations),
                selectinload(Tour.tour_images),
                selectinload(Tour.tour_dates),
            )
            .where(Tour.slug == slug, Tour.deleted_at.is_(None))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_published(
        self,
        db: AsyncSession,
        *,
        locale: str,
        skip: int = 0,
        limit: int = 12,
        difficulty: Optional[str] = None,
    ) -> tuple[list[Tour], int]:
        query = (
            select(Tour)
            .options(
                selectinload(Tour.tour_translations),
                selectinload(Tour.tour_images),
            )
            .where(Tour.status == "published", Tour.deleted_at.is_(None))
        )

        if difficulty:
            query = query.where(Tour.difficulty == difficulty)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Tour.avg_rating.desc().nullslast())
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all()), total


class CRUDTourDate(CRUDBase[TourDate]):
    def __init__(self):
        super().__init__(TourDate)

    async def get_by_tour(
        self, db: AsyncSession, tour_id: UUID
    ) -> list[TourDate]:
        result = await db.execute(
            select(TourDate)
            .where(TourDate.tour_id == tour_id)
            .order_by(TourDate.start_date)
        )
        return list(result.scalars().all())

    async def decrement_availability(
        self, db: AsyncSession, tour_date_id: UUID, amount: int
    ) -> Optional[TourDate]:
        """原子扣减库存，防超卖。"""
        result = await db.execute(
            select(TourDate).where(
                TourDate.id == tour_date_id,
                TourDate.availability >= amount,
            )
        )
        tour_date = result.scalar_one_or_none()
        if not tour_date:
            return None
        tour_date.availability -= amount
        await db.flush()
        return tour_date


crud_tour = CRUDTour()
crud_tour_date = CRUDTourDate()
