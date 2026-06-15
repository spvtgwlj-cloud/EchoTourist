"""AttractionTicket 景点门票类型模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AttractionTicket(Base):
    """景点门票类型 — 每个景点可以有多种门票（标准、VIP、儿童等）。"""

    __tablename__ = "attraction_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attraction_id = Column(
        UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticket_type = Column(String(50), nullable=False, default="standard")  # standard, vip, child
    price = Column(Float, nullable=False, default=0)
    currency = Column(String(3), default="USD")
    availability = Column(Integer, nullable=False, default=0)  # 剩余库存
    status = Column(String(20), default="available")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    attraction = relationship("Attraction", back_populates="tickets")

    __table_args__ = (UniqueConstraint("attraction_id", "ticket_type", name="uq_attraction_ticket_type"),)
