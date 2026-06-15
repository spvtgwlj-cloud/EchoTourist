"""AttractionWishlist 景点收藏 Schema。"""

import uuid
from typing import Optional

from pydantic import BaseModel


class AttractionWishlistItemResponse(BaseModel):
    id: uuid.UUID
    attraction_id: uuid.UUID
    attraction_name: Optional[str] = None
    attraction_slug: Optional[str] = None
    attraction_image: Optional[str] = None
    rating: int = 0
    created_at: str = ""

    model_config = {"from_attributes": True}


class AttractionWishlistResponse(BaseModel):
    items: list[AttractionWishlistItemResponse]
