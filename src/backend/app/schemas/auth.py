from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    is_admin: bool = False
    created_at: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
