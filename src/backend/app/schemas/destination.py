"""Destination 目的地 Schema。"""

from pydantic import BaseModel
from typing import Optional
import uuid


class DestinationResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    tour_count: int = 0
    locale: str = "en"

    model_config = {"from_attributes": True}


class DestinationListResponse(BaseModel):
    destinations: list[DestinationResponse]
