"""Order 相关数据访问操作。"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.order import Order, OrderPassenger


class CRUDOrder(CRUDBase[Order]):
    def __init__(self):
        super().__init__(Order)

    async def get_by_order_no(self, db: AsyncSession, order_no: str) -> Optional[Order]:
        result = await db.execute(
            select(Order).where(Order.order_no == order_no)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Order]:
        result = await db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(selectinload(Order.passengers))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_stripe_session(
        self, db: AsyncSession, session_id: str
    ) -> Optional[Order]:
        result = await db.execute(
            select(Order).where(Order.stripe_session_id == session_id)
        )
        return result.scalar_one_or_none()


crud_order = CRUDOrder()
