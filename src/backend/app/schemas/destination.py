"""Destination 目的地 Schema。"""

import uuid
from typing import Optional

from pydantic import BaseModel


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
