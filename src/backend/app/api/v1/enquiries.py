"""Enquiry 咨询表单 API 路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.enquiry import crud_enquiry
from app.database import get_db
from app.schemas.enquiry import EnquiryCreate, EnquiryResponse

router = APIRouter(prefix="/enquiries", tags=["enquiries"])


@router.post("", response_model=EnquiryResponse)
async def create_enquiry(
    req: EnquiryCreate,
    db: AsyncSession = Depends(get_db),
):
    """公开接口：提交咨询表单。"""
    return await crud_enquiry.create(
        db,
        name=req.name,
        email=req.email,
        phone=req.phone,
        destination=req.destination,
        pax_count=req.pax_count,
        message=req.message,
        status="new",
    )
