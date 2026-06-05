"""Attraction 景点 API。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.attraction import AttractionResponse, AttractionListResponse, AttractionTicketResponse
from app.crud.attraction import crud_attraction
from app.crud.destination import crud_destination
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/destinations", tags=["attractions"])


@router.get("/{slug}/attractions", response_model=AttractionListResponse)
async def list_attractions(
    slug: str,
    locale: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    """获取指定目的地下的所有活跃景点（按 sort_order 排序）。"""
    # 先校验目的地是否存在
    dest = await crud_destination.get_by_slug(db, slug, locale)
    if not dest:
        raise NotFoundException(detail="Destination not found")

    items = await crud_attraction.get_by_destination(db, dest["id"], locale)
    attractions = [
        AttractionResponse(
            id=item["id"],
            slug=item["slug"],
            destination_id=item["destination_id"],
            name=item["name"],
            description=item["description"],
            image_url=item["image_url"],
            sort_order=item["sort_order"],
            rating=item["rating"],
            ticket_price=item.get("ticket_price", 0),
            ticket_currency=item.get("ticket_currency", "USD"),
            tickets=[
                AttractionTicketResponse(**t) for t in item.get("tickets", [])
            ],
            locale=locale,
        )
        for item in items
    ]
    return AttractionListResponse(attractions=attractions)
