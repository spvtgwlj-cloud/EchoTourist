"""Wishlist 收藏 Schema。"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class WishlistItemResponse(BaseModel):
    id: uuid.UUID
    tour_id: uuid.UUID
    tour_name: Optional[str] = None
    tour_slug: Optional[str] = None
    tour_image: Optional[str] = None
    start_price: float = 0
    currency: str = "USD"
    avg_rating: float = 0
    created_at: str = ""

    model_config = {"from_attributes": True}


class WishlistResponse(BaseModel):
    items: list[WishlistItemResponse]
