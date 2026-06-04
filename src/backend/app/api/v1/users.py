"""用户资料管理 API。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.crud.user import crud_user
from app.models.user import User
from app.models.review import Review
from app.models.order import Order
from app.schemas.user import UserProfileUpdate, UserProfileResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Count reviews and orders
    review_result = await db.execute(
        select(func.count(Review.id)).where(Review.user_id == user.id)
    )
    order_result = await db.execute(
        select(func.count(Order.id)).where(Order.user_id == user.id)
    )

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        locale=user.locale or "en",
        is_admin=user.is_admin or False,
        created_at=user.created_at.isoformat() if user.created_at else "",
        review_count=review_result.scalar() or 0,
        order_count=order_result.scalar() or 0,
    )


@router.patch("/me/profile", response_model=UserProfileResponse)
async def update_profile(
    req: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = req.model_dump(exclude_none=True)
    if update_data:
        await crud_user.update_profile(db, user=user, profile_data=update_data)
        await db.refresh(user)
    # Reload counts
    review_result = await db.execute(
        select(func.count(Review.id)).where(Review.user_id == user.id)
    )
    order_result = await db.execute(
        select(func.count(Order.id)).where(Order.user_id == user.id)
    )
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        locale=user.locale or "en",
        is_admin=user.is_admin or False,
        created_at=user.created_at.isoformat() if user.created_at else "",
        review_count=review_result.scalar() or 0,
        order_count=order_result.scalar() or 0,
    )
