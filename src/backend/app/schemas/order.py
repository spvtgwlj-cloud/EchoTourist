from pydantic import BaseModel
from typing import Optional
from datetime import date
import uuid


class BookingRequest(BaseModel):
    tour_id: uuid.UUID
    tour_date_id: uuid.UUID
    pax_count: int
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    special_requests: Optional[str] = None
    locale: str = "en"


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_no: str
    tour_id: uuid.UUID
    tour_name: Optional[str] = None
    tour_date: str
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
