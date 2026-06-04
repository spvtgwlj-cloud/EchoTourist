"""User 相关数据访问操作。"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.user import User
from app.core.security import hash_password


class CRUDUser(CRUDBase[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, db: AsyncSession, google_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create_with_password(
        self, db: AsyncSession, *, email: str, name: str, password: str
    ) -> User:
        user = User(
            email=email,
            name=name,
            hashed_password=hash_password(password),
        )
        db.add(user)
        await db.flush()
        return user

    async def update_profile(
        self, db: AsyncSession, *, user: User, profile_data: dict
    ) -> User:
        updatable = ("name", "avatar_url", "locale")
        for field, value in profile_data.items():
            if field in updatable and value is not None:
                setattr(user, field, value)
        await db.flush()
        return user


crud_user = CRUDUser()
