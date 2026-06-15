"""Attraction 景点模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Attraction(Base):
    """景点 — 隶属于某一目的地（城市），如故宫隶属于北京。"""

    __tablename__ = "attractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    destination_id = Column(
        UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url = Column(String(500))
    sort_order = Column(SmallInteger, default=0)
    rating = Column(SmallInteger, default=0)  # 1-5
    status = Column(String(20), default="active")
    # Ticket/ordering fields
    ticket_price = Column(Float, default=0)  # 展示价格（最低价 or 标准价）
    ticket_currency = Column(String(3), default="USD")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    translations = relationship("AttractionTranslation", backref="attraction", lazy="selectin")
    destination = relationship("Destination", backref="attractions")
    tickets = relationship("AttractionTicket", back_populates="attraction", cascade="all, delete-orphan")
    media = relationship(
        "AttractionMedia", back_populates="attraction",
        cascade="all, delete-orphan", order_by="AttractionMedia.sort_order",
    )


class AttractionTranslation(Base):
    """景点多语言翻译。"""

    __tablename__ = "attraction_translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attraction_id = Column(
        UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False
    )
    locale = Column(String(10), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    ticket_info = Column(String(300))
    opening_hours = Column(String(200))
    meta_title = Column(String(200))
    meta_description = Column(String(300))
