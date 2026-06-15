"""Review 评价 API。"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.exceptions import ValidationException
from app.crud.review import crud_review
from app.database import get_db
from app.models.tour import Tour, TourTranslation
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse)
async def create_review(
    req: ReviewCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not 1 <= req.rating <= 5:
        raise ValidationException(detail="Rating must be between 1 and 5")
    review = await crud_review.create_review(
        db,
        tour_id=req.tour_id,
        user_id=user.id,
        rating=req.rating,
        title=req.title,
        comment=req.comment,
        locale=req.locale,
    )

    # ── 异步发送评价通知给所有管理员 ────────────────
    try:
        # 惰性导入避免与 payment_service 的循环依赖
        from app.tasks.email_tasks import send_review_notification

        # 获取产品名称
        trans_result = await db.execute(
            select(TourTranslation).where(
                TourTranslation.tour_id == req.tour_id,
                TourTranslation.locale == "en",
            )
        )
        translation = trans_result.scalar_one_or_none()
        tour_name = translation.name if translation else f"Tour {str(req.tour_id)[:8]}"

        # 获取产品 slug
        tour_result = await db.execute(
            select(Tour.slug).where(Tour.id == req.tour_id)
        )
        tour_slug = tour_result.scalar_one_or_none() or str(req.tour_id)

        # 获取所有管理员的邮箱
        admin_result = await db.execute(
            select(User.email).where(User.is_admin.is_(True), User.is_active.is_(True))
        )
        admin_emails = admin_result.scalars().all()

        for admin_email in admin_emails:
            send_review_notification.delay(
                tour_name=tour_name,
                tour_slug=tour_slug,
                reviewer_name=user.name or "A customer",
                rating=req.rating,
                title=req.title,
                comment=req.comment,
                admin_email=admin_email,
            )
        if admin_emails:
            logger.info(
                "Dispatched review notification for tour %s to %d admin(s)",
                req.tour_id, len(admin_emails),
            )
    except Exception as e:
        logger.error("Failed to dispatch review notification: %s", e)

    return ReviewResponse(
        id=review.id,
        tour_id=review.tour_id,
        user_id=review.user_id,
        user_name=user.name,
        rating=review.rating,
        title=review.title,
        comment=review.comment,
        locale=review.locale or "en",
        status=review.status or "pending",
        created_at=review.created_at.isoformat() if review.created_at else "",
    )


@router.get("/tour/{tour_id}", response_model=ReviewListResponse)
async def get_tour_reviews(
    tour_id: str,
    locale: str = Query("en"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    try:
        uid = uuid.UUID(tour_id)
    except ValueError:
        raise ValidationException(detail="Invalid tour_id")

    skip = (page - 1) * page_size
    reviews, total, avg_rating = await crud_review.get_tour_reviews(
        db, uid, skip=skip, limit=page_size
    )

    review_responses = [
        ReviewResponse(
            id=r["id"],
            tour_id=r["tour_id"],
            user_id=r["user_id"],
            user_name=r["user_name"],
            rating=r["rating"],
            title=r["title"],
            comment=r["comment"],
            locale=r["locale"],
            status=r["status"],
            created_at=r["created_at"],
        )
        for r in reviews
    ]

    return ReviewListResponse(
        reviews=review_responses,
        total=total,
        avg_rating=avg_rating,
    )
