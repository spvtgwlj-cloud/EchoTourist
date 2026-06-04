"""API 集成测试 —— 认证（通过运行中的 Docker 服务）。"""

import uuid

import pytest
from httpx import AsyncClient


class TestAuthAPI:
    """认证 API 完整测试。"""

    # ============================================================
    # 注册
    # ============================================================

    async def test_register_success(self, api_client: AsyncClient):
        """功能测试：注册成功返回 JWT + 用户信息。"""
        email = f"api_test_{uuid.uuid4().hex[:8]}@example.com"
        response = await api_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "StrongPass1!", "name": "API Test User"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == email
        assert data["user"]["name"] == "API Test User"

    async def test_register_duplicate(self, api_client: AsyncClient):
        """鲁棒性测试：重复注册返回 409。"""
        email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
        await api_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Pass1234!", "name": "First"},
        )
        response = await api_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Pass5678!", "name": "Second"},
        )
        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "CONFLICT"

    async def test_register_missing_fields(self, api_client: AsyncClient):
        """边界测试：缺少必填字段返回 422。"""
        response = await api_client.post(
            "/api/v1/auth/register",
            json={"email": f"miss_{uuid.uuid4().hex[:8]}@example.com", "name": "Missing"},
        )
        assert response.status_code == 422

        response = await api_client.post(
            "/api/v1/auth/register",
            json={"password": "test1234", "name": "Missing"},
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, api_client: AsyncClient):
        """边界测试：无效邮箱返回 422。"""
        response = await api_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "test1234", "name": "Bad"},
        )
        assert response.status_code == 422

    async def test_register_empty_body(self, api_client: AsyncClient):
        """边界测试：空请求体返回 422。"""
        response = await api_client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

    # ============================================================
    # 登录
    # ============================================================

    async def test_login_success(self, api_client: AsyncClient, factory):
        """功能测试：登录成功返回 JWT。"""
        reg_data = factory.valid_register_data()
        await api_client.post("/api/v1/auth/register", json=reg_data)

        response = await api_client.post(
            "/api/v1/auth/login",
            json={"email": reg_data["email"], "password": reg_data["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == reg_data["email"]

    async def test_login_wrong_password(self, api_client: AsyncClient):
        """鲁棒性测试：错误密码返回 401。"""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, api_client: AsyncClient):
        """鲁棒性测试：不存在的用户返回 401。"""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": f"nonexistent_{uuid.uuid4().hex[:8]}@example.com",
                "password": "pass1234",
            },
        )
        assert response.status_code == 401

    async def test_login_empty_password(self, api_client: AsyncClient):
        """边界测试：空密码 — 空字符串被 Pydantic 接受（str 类型），返回 401。"""
        response = await api_client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": ""},
        )
        # 空密码是有效 str，服务端返回 401（用户不存在）
        assert response.status_code in (401, 422)

    # ============================================================
    # 获取当前用户 (GET /me)
    # ============================================================

    async def test_get_me_with_token(self, api_client: AsyncClient, factory):
        """功能测试：认证后获取当前用户信息。"""
        reg_data = factory.valid_register_data()
        reg_resp = await api_client.post("/api/v1/auth/register", json=reg_data)
        token = reg_resp.json()["access_token"]

        response = await api_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == reg_data["email"]
        assert "id" in data
        assert "created_at" in data

    async def test_get_me_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证时返回 401。"""
        response = await api_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, api_client: AsyncClient):
        """鲁棒性测试：无效 token 返回 401。"""
        response = await api_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 401

    async def test_get_me_expired_token(self, api_client: AsyncClient):
        """鲁棒性测试：过期 token 返回 401。"""
        from app.core.security import create_access_token
        from datetime import timedelta

        expired_token = create_access_token(
            data={"sub": str(uuid.uuid4())},
            expires_delta=timedelta(seconds=-1),
        )
        response = await api_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
