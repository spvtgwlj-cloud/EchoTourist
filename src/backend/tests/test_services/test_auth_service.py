"""Service 层测试 —— Auth。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import auth_service
from app.core.exceptions import ConflictException, AuthenticationException
from app.models.user import User


class TestAuthService:
    """Auth Service 业务逻辑测试。"""

    async def test_register_success(self, db_session: AsyncSession):
        """功能测试：注册成功返回 JWT 和用户信息。"""
        email = f"svc_test_{uuid.uuid4().hex[:8]}@example.com"
        result = await auth_service.register(
            db_session,
            email=email,
            password="StrongPass1!",
            name="Service Test User",
        )
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.user.email == email
        assert result.user.name == "Service Test User"

    async def test_register_duplicate_email(self, db_session: AsyncSession, test_user: User):
        """鲁棒性测试：重复注册抛出 ConflictException。"""
        with pytest.raises(ConflictException) as exc:
            await auth_service.register(
                db_session,
                email=test_user.email,
                password="SomePass123",
                name="Duplicate User",
            )
        assert "Email already registered" in str(exc.value.detail)

    async def test_login_success(self, db_session: AsyncSession, test_user: User):
        """功能测试：登录成功返回 JWT。"""
        result = await auth_service.login(
            db_session,
            email=test_user.email,
            password="testpass123",
        )
        assert result.access_token is not None
        assert result.user.id == test_user.id

    async def test_login_wrong_password(self, db_session: AsyncSession, test_user: User):
        """鲁棒性测试：错误密码抛出 AuthenticationException。"""
        with pytest.raises(AuthenticationException):
            await auth_service.login(
                db_session,
                email=test_user.email,
                password="wrongpassword",
            )

    async def test_login_nonexistent_user(self, db_session: AsyncSession):
        """鲁棒性测试：不存在的用户抛出 AuthenticationException。"""
        with pytest.raises(AuthenticationException):
            await auth_service.login(
                db_session,
                email=f"nonexistent_{uuid.uuid4().hex[:8]}@example.com",
                password="somepassword",
            )

    async def test_get_me(self, db_session: AsyncSession, test_user: User):
        """功能测试：获取当前用户信息。"""
        result = await auth_service.get_me(test_user)
        assert result.id == test_user.id
        assert result.email == test_user.email
        assert result.name == test_user.name

    async def test_get_me_returns_iso_datetime(self, db_session: AsyncSession, test_user: User):
        """功能测试：created_at 应为 ISO 格式字符串。"""
        result = await auth_service.get_me(test_user)
        assert isinstance(result.created_at, str)
        assert "T" in result.created_at  # ISO 格式包含 T
