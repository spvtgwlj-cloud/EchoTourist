"""AttractionWishlist 景点收藏 API。"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.crud.attraction_wishlist import crud_attraction_wishlist
from app.models.user import User
from app.schemas.attraction_wishlist import AttractionWishlistResponse, AttractionWishlistItemResponse

router = APIRouter(prefix="/wishlist/attractions", tags=["wishlist"])


@router.get("", response_model=AttractionWishlistResponse)
async def get_attraction_wishlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await crud_attraction_wishlist.get_user_wishlist(db, user.id, locale=user.locale or "en")
    wishlist_items = [
        AttractionWishlistItemResponse(
            id=item["id"],
            attraction_id=item["attraction_id"],
            attraction_name=item["attraction_name"],
            attraction_slug=item["attraction_slug"],
            attraction_image=item["attraction_image"],
            rating=item["rating"],
            created_at=item["created_at"],
        )
        for item in items
    ]
    return AttractionWishlistResponse(items=wishlist_items)


@router.post("/{attraction_id}", response_model=dict)
async def add_attraction_to_wishlist(
    attraction_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        uid = uuid.UUID(attraction_id)
    except ValueError:
        from app.core.exceptions import ValidationException
        raise ValidationException(detail="Invalid attraction_id")

    wl = await crud_attraction_wishlist.add(db, user.id, uid)
    return {"status": "ok", "id": str(wl.id)}


@router.delete("/{attraction_id}", response_model=dict)
async def remove_attraction_from_wishlist(
    attraction_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        uid = uuid.UUID(attraction_id)
    except ValueError:
        from app.core.exceptions import ValidationException
        raise ValidationException(detail="Invalid attraction_id")

    removed = await crud_attraction_wishlist.remove(db, user.id, uid)
    return {"status": "ok" if removed else "not_found"}
