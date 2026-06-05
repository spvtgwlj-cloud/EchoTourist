"""AttractionTicket 景点门票 CRUD 操作。"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.attraction_ticket import AttractionTicket


class CRUDAttractionTicket(CRUDBase[AttractionTicket]):
    def __init__(self):
        super().__init__(AttractionTicket)

    async def get_by_attraction(
        self, db: AsyncSession, attraction_id: UUID
    ) -> list[AttractionTicket]:
        result = await db.execute(
            select(AttractionTicket)
            .where(
                AttractionTicket.attraction_id == attraction_id,
                AttractionTicket.status == "available",
            )
            .order_by(AttractionTicket.price)
        )
        return list(result.scalars().all())

    async def decrement_availability(
        self, db: AsyncSession, ticket_id: UUID, amount: int
    ) -> Optional[AttractionTicket]:
        """原子扣减门票库存，防超卖。"""
        result = await db.execute(
            select(AttractionTicket).where(
                AttractionTicket.id == ticket_id,
                AttractionTicket.availability >= amount,
                AttractionTicket.status == "available",
            )
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            return None
        ticket.availability -= amount
        await db.flush()
        return ticket


crud_attraction_ticket = CRUDAttractionTicket()
