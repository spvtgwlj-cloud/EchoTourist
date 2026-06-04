"""User 用户 Profile Schema。"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    locale: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    locale: str = "en"
    is_admin: bool = False
    created_at: str = ""
    review_count: int = 0
    order_count: int = 0

    model_config = {"from_attributes": True}
