import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, SmallInteger, DateTime, Date, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Tour(Base):
    __tablename__ = "tours"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(200), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="draft")
    type = Column(String(30), nullable=False, default="group_tour")
    duration_days = Column(SmallInteger, nullable=False)
    duration_nights = Column(SmallInteger, nullable=False, default=0)
    max_pax = Column(SmallInteger)
    min_pax = Column(SmallInteger, default=1)
    start_price = Column(Float, default=0)
    currency = Column(String(3), default="USD")
    difficulty = Column(String(20), default="easy")
    highlights = Column(PG_ARRAY(Text), default=list)
    includes = Column(PG_ARRAY(Text), default=list)
    excludes = Column(PG_ARRAY(Text), default=list)
    sort_order = Column(SmallInteger, default=0)
    serial_number = Column(String(10))  # 4位数字序列号，如 0001
    destination_ids = Column(PG_ARRAY(UUID(as_uuid=True)), default=list)
    avg_rating = Column(Float, default=0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

    tour_translations = relationship("TourTranslation", backref="tour", lazy="selectin")
    tour_images = relationship("TourImage", backref="tour", lazy="selectin", order_by="TourImage.sort_order")
    tour_dates = relationship("TourDate", backref="tour", lazy="selectin")


class TourTranslation(Base):
    __tablename__ = "tour_translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False)
    locale = Column(String(10), nullable=False)
    name = Column(String(300), nullable=False)
    subtitle = Column(String(500))
    description = Column(Text)
    itinerary = Column(JSON)
    highlights = Column(JSON)
    includes = Column(JSON)
    excludes = Column(JSON)
    meta_title = Column(String(200))
    meta_description = Column(String(300))



class TourDate(Base):
    __tablename__ = "tour_dates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    price_per_pax = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    availability = Column(SmallInteger, nullable=False, default=0)
    status = Column(String(20), default="available")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TourImage(Base):
    __tablename__ = "tour_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(500), nullable=False)
    alt_text = Column(String(300))
    sort_order = Column(SmallInteger, default=0)
