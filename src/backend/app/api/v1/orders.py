import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.order import BookingRequest, OrderListResponse, OrderResponse
from app.services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
async def create_order(
    req: BookingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.create_booking(db, req=req, user=user)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.list_user_orders(db, user)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await order_service.get_order(db, order_id, user)
