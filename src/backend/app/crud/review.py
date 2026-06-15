"""Review CRUD 操作。"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, ValidationException
from app.crud.base import CRUDBase
from app.models.order import Order
from app.models.review import Review
from app.models.tour import Tour
from app.models.user import User


class CRUDReview(CRUDBase[Review]):
    def __init__(self):
        super().__init__(Review)

    async def create_review(
        self,
        db: AsyncSession,
        *,
        tour_id: uuid.UUID,
        user_id: uuid.UUID,
        rating: int,
        title: str | None = None,
        comment: str | None = None,
        locale: str = "en",
    ) -> Review:
        # Check for duplicate review by the same user for the same tour
        existing = await db.execute(
            select(Review).where(
                Review.tour_id == tour_id,
                Review.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(detail="You have already reviewed this tour")

        # 只有已确认（已支付）订单的用户才能评价
        order_check = await db.execute(
            select(Order.id).where(
                Order.user_id == user_id,
                Order.tour_id == tour_id,
                Order.status == "confirmed",
                Order.payment_status == "paid",
            ).limit(1)
        )
        if not order_check.scalar_one_or_none():
            raise ValidationException(
                detail="You must have a confirmed booking to review this tour"
            )

        review = Review(
            tour_id=tour_id,
            user_id=user_id,
            rating=rating,
            title=title,
            comment=comment,
            locale=locale,
            status="approved",  # auto-approve for now
        )
        db.add(review)
        await db.flush()

        # Recalculate avg_rating
        stats = await db.execute(
            select(
                func.avg(Review.rating).label("avg"),
                func.count(Review.id).label("cnt"),
            ).where(Review.tour_id == tour_id, Review.status == "approved")
        )
        row = stats.one()
        if row.avg is not None:
            await db.execute(
                Tour.__table__.update()
                .where(Tour.id == tour_id)
                .values(avg_rating=round(float(row.avg), 1), review_count=row.cnt)
            )
            await db.flush()

        return review

    async def get_tour_reviews(
        self,
        db: AsyncSession,
        tour_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 20,
        status: str | None = "approved",
    ) -> tuple[list[dict], int, float]:
        query = (
            select(Review, User.name.label("user_name"))
            .outerjoin(User, Review.user_id == User.id)
            .where(Review.tour_id == tour_id)
        )
        if status:
            query = query.where(Review.status == status)
        query = query.order_by(Review.created_at.desc())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        avg_result = await db.execute(
            select(func.avg(Review.rating)).where(
                Review.tour_id == tour_id,
                Review.status == "approved",
            )
        )
        avg_rating = avg_result.scalar() or 0.0

        reviews = []
        for row in rows:
            r = row.Review
            reviews.append({
                "id": r.id,
                "tour_id": r.tour_id,
                "user_id": r.user_id,
                "user_name": getattr(row, "user_name", None),
                "rating": r.rating,
                "title": r.title,
                "comment": r.comment,
                "locale": r.locale,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            })

        return reviews, total, round(float(avg_rating), 1)


crud_review = CRUDReview()
