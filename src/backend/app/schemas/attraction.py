"""Attraction 景点 Schema。"""

from pydantic import BaseModel
from typing import Optional
import uuid


class AttractionResponse(BaseModel):
    id: uuid.UUID
    slug: str
    destination_id: uuid.UUID
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    rating: int = 0
    locale: str = "en"

    model_config = {"from_attributes": True}


class AttractionListResponse(BaseModel):
    attractions: list[AttractionResponse]
