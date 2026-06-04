"""Destination 目的地 API。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.crud.destination import crud_destination
from app.crud.tour import crud_tour
from app.schemas.destination import DestinationResponse, DestinationListResponse
from app.schemas.tour import TourListResponse
from app.core.exceptions import NotFoundException
from app.services.tour_service import tour_service

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("", response_model=DestinationListResponse)
async def list_destinations(
    locale: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    items = await crud_destination.get_active(db, locale=locale)
    destinations = [
        DestinationResponse(
            id=item["id"],
            slug=item["slug"],
            name=item["name"],
            description=item["description"],
            image_url=item["image_url"],
            tour_count=item["tour_count"],
            locale=locale,
        )
        for item in items
    ]
    return DestinationListResponse(destinations=destinations)


@router.get("/{slug}", response_model=DestinationResponse)
async def get_destination(
    slug: str,
    locale: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    dest = await crud_destination.get_by_slug(db, slug, locale=locale)
    if not dest:
        raise NotFoundException(detail="Destination not found")
    return DestinationResponse(
        id=dest["id"],
        slug=dest["slug"],
        name=dest["name"],
        description=dest["description"],
        image_url=dest["image_url"],
        tour_count=dest["tour_count"],
        locale=locale,
    )


@router.get("/{slug}/tours", response_model=TourListResponse)
async def get_destination_tours(
    slug: str,
    locale: str = Query("en"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    dest = await crud_destination.get_by_slug(db, slug, locale=locale)
    if not dest:
        raise NotFoundException(detail="Destination not found")
    # Use tour_service which filters by published status and locale
    return await tour_service.list_tours(
        db, locale=locale, page=page, page_size=page_size
    )
