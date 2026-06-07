from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.tour import TourResponse, TourListResponse, TourDateListResponse
from app.services.tour_service import tour_service
from typing import Optional
import uuid

router = APIRouter(prefix="/tours", tags=["tours"])


@router.get("", response_model=TourListResponse)
async def list_tours(
    locale: str = Query("en"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    difficulty: Optional[str] = None,
    theme: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await tour_service.list_tours(
        db,
        locale=locale,
        page=page,
        page_size=page_size,
        difficulty=difficulty,
        theme=theme,
    )


@router.get("/{slug_or_id}", response_model=TourResponse)
async def get_tour(
    slug_or_id: str,
    locale: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    return await tour_service.get_tour(db, slug_or_id, locale)


@router.get("/{tour_id}/dates", response_model=TourDateListResponse)
async def get_tour_dates(
    tour_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await tour_service.get_tour_dates(db, tour_id)
