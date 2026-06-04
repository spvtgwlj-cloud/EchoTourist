"""Review 评分/评价 Schema。"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class ReviewCreate(BaseModel):
    tour_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None
    locale: str = "en"


class ReviewResponse(BaseModel):
    id: uuid.UUID
    tour_id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    locale: str = "en"
    status: str = "pending"
    created_at: str = ""

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
    avg_rating: float = 0.0
