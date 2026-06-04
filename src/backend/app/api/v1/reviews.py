"""Review 评价 API。"""

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.crud.review import crud_review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewListResponse
from app.core.exceptions import NotFoundException, ValidationException

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
