import uuid
from typing import Optional

from pydantic import BaseModel, Field


class BookingRequest(BaseModel):
    tour_id: Optional[uuid.UUID] = None
    tour_date_id: Optional[uuid.UUID] = None
    attraction_id: Optional[uuid.UUID] = None
    attraction_ticket_id: Optional[uuid.UUID] = None
    pax_count: int = Field(gt=0, description="Number of passengers, must be >= 1")
    contact_name: str = Field(max_length=100, description="Contact name, max 100 chars")
    contact_email: str = Field(max_length=200, description="Contact email, max 200 chars")
    contact_phone: Optional[str] = None
    special_requests: Optional[str] = None
    locale: str = "en"


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_no: str
    tour_id: Optional[uuid.UUID] = None
    tour_name: Optional[str] = None
    tour_date: str = ""
    attraction_id: Optional[uuid.UUID] = None
    attraction_name: Optional[str] = None
    status: str
    pax_count: int
    total: float
    currency: str
    contact_name: str
    contact_email: str
    created_at: str
    payment_status: Optional[str] = None

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]


class PaymentIntentResponse(BaseModel):
    client_secret: str = ""
    session_id: str
