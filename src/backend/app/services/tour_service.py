"""Tour 业务逻辑服务。"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.tour import crud_tour, crud_tour_date
from app.core.exceptions import NotFoundException
from app.cache.decorators import cache_result
from app.schemas.tour import (
    TourResponse,
    TourListResponse,
    TourDateResponse,
    TourDateListResponse,
    ItineraryDay,
)


class TourService:
    @staticmethod
    async def _build_response(tour, locale: str) -> TourResponse:
        """将 Tour ORM 对象构建为 TourResponse。"""
        translation = None
        if tour.tour_translations:
            for t in tour.tour_translations:
                if t.locale == locale:
                    translation = t
                    break
            if not translation:
                translation = tour.tour_translations[0]

        itinerary = []
        if translation and translation.itinerary:
            itinerary = [ItineraryDay(**day) for day in translation.itinerary]

        images = [img.url for img in (tour.tour_images or [])]

        return TourResponse(
            id=tour.id,
            slug=tour.slug,
            name=translation.name if translation else tour.slug,
            subtitle=translation.subtitle if translation else None,
            description=translation.description if translation else None,
            duration_days=tour.duration_days,
            duration_nights=tour.duration_nights,
            start_price=tour.start_price or 0,
            currency=tour.currency or "USD",
            max_pax=tour.max_pax,
            min_pax=tour.min_pax or 1,
            difficulty=tour.difficulty or "easy",
            avg_rating=tour.avg_rating or 0,
            review_count=tour.review_count or 0,
            images=images,
            highlights=tour.highlights or [],
            includes=tour.includes or [],
            excludes=tour.excludes or [],
            itinerary=itinerary,
            status=tour.status,
            locale=locale,
        )

    @cache_result(ttl=120)
    async def list_tours(
        self,
        db: AsyncSession,
        *,
        locale: str = "en",
        page: int = 1,
        page_size: int = 12,
        difficulty: Optional[str] = None,
    ) -> TourListResponse:
        skip = (page - 1) * page_size
        tours, total = await crud_tour.get_published(
            db,
            locale=locale,
            skip=skip,
            limit=page_size,
            difficulty=difficulty,
        )
        tour_responses = [await self._build_response(t, locale) for t in tours]
        return TourListResponse(
            tours=tour_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    @cache_result(ttl=300)
    async def get_tour(
        self,
        db: AsyncSession,
        slug_or_id: str,
        locale: str = "en",
    ) -> TourResponse:
        try:
            uid = UUID(slug_or_id)
            tour = await crud_tour.get_with_details(db, uid, locale)
        except ValueError:
            tour = await crud_tour.get_by_slug(db, slug_or_id, locale)

        if not tour:
            raise NotFoundException(detail="Tour not found")
        return await self._build_response(tour, locale)

    @cache_result(ttl=60)
    async def get_tour_dates(
        self, db: AsyncSession, tour_id: UUID
    ) -> TourDateListResponse:
        dates = await crud_tour_date.get_by_tour(db, tour_id)
        return TourDateListResponse(
            dates=[TourDateResponse.model_validate(d) for d in dates]
        )


tour_service = TourService()
