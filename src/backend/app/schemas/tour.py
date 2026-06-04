from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import uuid


class ItineraryDay(BaseModel):
    day: int
    title: str
    description: str
    meals: list[str] = []
    accommodation: Optional[str] = None


class TourResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str = ""
    subtitle: Optional[str] = None
    description: Optional[str] = None
    duration_days: int
    duration_nights: int
    start_price: float
    currency: str
    max_pax: Optional[int] = None
    min_pax: int
    difficulty: str
    avg_rating: float
    review_count: int
    images: list[str] = []
    highlights: list[str] = []
    includes: list[str] = []
    excludes: list[str] = []
    itinerary: Optional[list[ItineraryDay]] = None
    destination_name: Optional[str] = None
    category_name: Optional[str] = None
    status: str
    locale: str

    model_config = {"from_attributes": True}


class TourListResponse(BaseModel):
    tours: list[TourResponse]
    total: int
    page: int = 1
    page_size: int = 12


class TourDateResponse(BaseModel):
    id: uuid.UUID
    tour_id: uuid.UUID
    start_date: date
    end_date: date
    price_per_pax: float
    currency: str
    availability: int
    status: str

    model_config = {"from_attributes": True}


class TourDateListResponse(BaseModel):
    dates: list[TourDateResponse]
