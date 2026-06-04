"""Wishlist/收藏 API。"""

import uuid

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.crud.wishlist import crud_wishlist
from app.models.user import User
from app.schemas.wishlist import WishlistResponse, WishlistItemResponse

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=WishlistResponse)
async def get_wishlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await crud_wishlist.get_user_wishlist(db, user.id, locale=user.locale or "en")
    wishlist_items = [
        WishlistItemResponse(
            id=item["id"],
            tour_id=item["tour_id"],
            tour_name=item["tour_name"],
            tour_slug=item["tour_slug"],
            tour_image=item["tour_image"],
            start_price=item["start_price"],
            currency=item["currency"],
            avg_rating=item["avg_rating"],
            created_at=item["created_at"],
        )
        for item in items
    ]
    return WishlistResponse(items=wishlist_items)


@router.post("/{tour_id}", response_model=dict)
async def add_to_wishlist(
    tour_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        uid = uuid.UUID(tour_id)
    except ValueError:
        from app.core.exceptions import ValidationException
        raise ValidationException(detail="Invalid tour_id")

    wl = await crud_wishlist.add(db, user.id, uid)
    return {"status": "ok", "id": str(wl.id)}


@router.delete("/{tour_id}", response_model=dict)
async def remove_from_wishlist(
    tour_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        uid = uuid.UUID(tour_id)
    except ValueError:
        from app.core.exceptions import ValidationException
        raise ValidationException(detail="Invalid tour_id")

    removed = await crud_wishlist.remove(db, user.id, uid)
    return {"status": "ok" if removed else "not_found"}
