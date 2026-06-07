"""Enquiry 咨询表单的请求和响应模型。"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class EnquiryCreate(BaseModel):
    """公开提交咨询表单"""
    name: str = "咨询人"
    email: str
    phone: Optional[str] = None
    destination: Optional[str] = None
    pax_count: Optional[int] = None
    message: str = "咨询需求"


class EnquiryUpdate(BaseModel):
    """管理员更新咨询记录"""
    status: Optional[str] = None     # new | read | contacted | closed
    admin_notes: Optional[str] = None


class EnquiryResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: Optional[str] = None
    destination: Optional[str] = None
    pax_count: Optional[int] = None
    message: str
    status: str = "new"
    admin_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EnquiryListResponse(BaseModel):
    enquiries: list[EnquiryResponse]
    total: int
    page: int = 1
    page_size: int = 20
