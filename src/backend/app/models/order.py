import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, SmallInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id"), nullable=False)
    tour_date_id = Column(UUID(as_uuid=True), ForeignKey("tour_dates.id"))
    status = Column(String(30), nullable=False, default="pending")
    pax_count = Column(SmallInteger, nullable=False)
    subtotal = Column(Float, nullable=False)
    discount = Column(Float, default=0)
    tax = Column(Float, default=0)
    total = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    contact_name = Column(String(100))
    contact_email = Column(String(200))
    contact_phone = Column(String(30))
    special_requests = Column(Text)
    source = Column(String(30), default="web")
    locale = Column(String(10), default="en")
    stripe_session_id = Column(String(255))
    payment_status = Column(String(30), default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    passengers = relationship("OrderPassenger", backref="order", lazy="selectin")


class OrderPassenger(Base):
    __tablename__ = "order_passengers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    passport_number = Column(String(50))
    special_requirements = Column(Text)
