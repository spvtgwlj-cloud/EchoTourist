"""Attraction 景点 Schema。"""

import uuid
from typing import Optional

from pydantic import BaseModel


class AttractionMediaResponse(BaseModel):
    id: uuid.UUID
    url: str
    media_type: str = "image"
    alt_text: Optional[str] = None
    sort_order: int = 0

    model_config = {"from_attributes": True}


class AttractionTicketResponse(BaseModel):
    id: uuid.UUID
    attraction_id: uuid.UUID
    ticket_type: str = "standard"
    price: float = 0
    currency: str = "USD"
    availability: int = 0
    status: str = "available"

    model_config = {"from_attributes": True}


class AttractionResponse(BaseModel):
    id: uuid.UUID
    slug: str
    destination_id: uuid.UUID
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    rating: int = 0
    ticket_price: float = 0
    ticket_currency: str = "USD"
    tickets: list[AttractionTicketResponse] = []
    media: list[AttractionMediaResponse] = []
    locale: str = "en"

    model_config = {"from_attributes": True}


class AttractionListResponse(BaseModel):
    attractions: list[AttractionResponse]
