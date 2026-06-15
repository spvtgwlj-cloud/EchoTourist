"""认证业务逻辑服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, ConflictException
from app.core.security import create_access_token, verify_password
from app.crud.user import crud_user
from app.models.user import User
from app.schemas.auth import AuthResponse, UserResponse


class AuthService:
    @staticmethod
    def _build_auth_response(user: User) -> AuthResponse:
        token = create_access_token(data={"sub": str(user.id)})
        return AuthResponse(
            access_token=token,
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                avatar_url=user.avatar_url,
                is_admin=user.is_admin or False,
                created_at=user.created_at.isoformat() if user.created_at else "",
            ),
        )

    async def register(
        self, db: AsyncSession, *, email: str, password: str, name: str
    ) -> AuthResponse:
        existing = await crud_user.get_by_email(db, email)
        if existing:
            raise ConflictException(detail="Email already registered")
        user = await crud_user.create_with_password(
            db, email=email, name=name, password=password
        )
        return self._build_auth_response(user)

    async def login(
        self, db: AsyncSession, *, email: str, password: str
    ) -> AuthResponse:
        user = await crud_user.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password or ""):
            raise AuthenticationException(detail="Invalid email or password")
        return self._build_auth_response(user)

    async def get_me(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin or False,
            created_at=user.created_at.isoformat() if user.created_at else "",
        )


auth_service = AuthService()
