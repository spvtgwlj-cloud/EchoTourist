"""自定制旅程 Pydantic schemas（支持多段行程）。"""

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class BaseServiceResponse(BaseModel):
    id: uuid.UUID
    name: str
    name_zh: Optional[str] = None
    name_es: Optional[str] = None
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_zh: Optional[str] = None
    description_es: Optional[str] = None
    description_fr: Optional[str] = None
    unit_type: str  # per_day / per_pax / per_trip
    unit_price: float
    currency: str
    category: Optional[str] = None
    sort_order: int = 0
    status: str

    model_config = {"from_attributes": True}


class BaseServiceListResponse(BaseModel):
    services: list[BaseServiceResponse]
    total: int


class BaseServiceCreate(BaseModel):
    name: str
    name_zh: Optional[str] = None
    name_es: Optional[str] = None
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_zh: Optional[str] = None
    description_es: Optional[str] = None
    description_fr: Optional[str] = None
    unit_type: str = "per_day"
    unit_price: float = 0
    currency: str = "USD"
    category: Optional[str] = None
    sort_order: int = 0
    status: str = "active"


class CustomTourServiceInput(BaseModel):
    service_id: uuid.UUID
    quantity: int = 1


# ── 行程段 Input ──────────────────────────────────────────────

class SegmentInput(BaseModel):
    """一段行程的输入。"""
    destination_id: Optional[uuid.UUID] = None       # 可选：系统目的地
    custom_destination: Optional[str] = None          # 可选：客户自定义目的地
    start_date: date
    end_date: date
    attraction_ids: list[uuid.UUID] = []
    tour_ids: list[uuid.UUID] = []  # 选择的已有产品（多选）


class CustomTourCreateRequest(BaseModel):
    """用户提交自定制旅程请求（支持多段行程）。"""
    segments: list[SegmentInput] = Field(min_length=1, description="至少一段行程")
    pax_count: int = Field(gt=0, le=100)
    guide_language: Optional[str] = None
    services: list[CustomTourServiceInput] = []
    contact_name: str = Field(min_length=1, max_length=100)
    contact_email: str = Field(max_length=200)
    contact_phone: Optional[str] = None
    special_requests: Optional[str] = None
    locale: str = "en"


class CustomTourQuoteResponse(BaseModel):
    """报价响应（含自动计算明细）。"""
    subtotal: float
    currency: str
    breakdown: dict = {}


# ── 行程段 Response ──────────────────────────────────────────

class SegmentTourResponse(BaseModel):
    id: uuid.UUID
    tour_id: uuid.UUID
    tour_name: str = ""

    model_config = {"from_attributes": True}


class SegmentAttractionResponse(BaseModel):
    id: uuid.UUID
    attraction_id: uuid.UUID
    attraction_name: str = ""
    sort_order: int = 0

    model_config = {"from_attributes": True}


class SegmentResponse(BaseModel):
    id: uuid.UUID
    segment_order: int
    destination_id: Optional[uuid.UUID] = None
    destination_name: str = ""
    custom_destination: Optional[str] = None
    start_date: date
    end_date: date
    attractions: list[SegmentAttractionResponse] = []
    selected_tours: list[SegmentTourResponse] = []

    model_config = {"from_attributes": True}


class CustomTourServiceResponse(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    service_name: str = ""
    unit_type: str = "per_day"
    quantity: int
    unit_price_snapshot: float
    subtotal: float

    model_config = {"from_attributes": True}


class CustomTourRequestResponse(BaseModel):
    id: uuid.UUID
    request_no: str
    user_id: Optional[uuid.UUID] = None
    pax_count: int
    guide_language: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = None
    special_requests: Optional[str] = None
    subtotal: float = 0
    confirmed_price: Optional[float] = None
    currency: str = "USD"
    status: str
    admin_notes: Optional[str] = None
    locale: str = "en"
    segments: list[SegmentResponse] = []
    services: list[CustomTourServiceResponse] = []
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CustomTourRequestListResponse(BaseModel):
    requests: list[CustomTourRequestResponse]
    total: int
    page: int = 1
    page_size: int = 20
