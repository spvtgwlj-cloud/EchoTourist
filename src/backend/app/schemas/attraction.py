"""Attraction 景点 Schema。"""

from pydantic import BaseModel
from typing import Optional
import uuid


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
    locale: str = "en"

    model_config = {"from_attributes": True}


class AttractionListResponse(BaseModel):
    attractions: list[AttractionResponse]
