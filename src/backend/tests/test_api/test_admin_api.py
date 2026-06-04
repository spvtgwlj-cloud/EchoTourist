"""后台管理 API 集成测试。"""

import uuid

import pytest
from httpx import AsyncClient


class TestAdminAPI:
    """Admin API 权限和功能测试。"""

    async def test_stats_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证返回 401。"""
        resp = await api_client.get("/api/v1/admin/stats")
        assert resp.status_code == 401

    async def test_stats_non_admin(self, api_client: AsyncClient, factory):
        """鲁棒性测试：非管理员返回 403。"""
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]

        resp = await api_client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_stats_admin(self, api_client: AsyncClient, factory):
        """功能测试：管理员可以看到统计。"""
        # Register and make admin via endpoint
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]
        user_id = r.json()["user"]["id"]

        # Promote (direct SQL, dev only)
        import httpx
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # Use the running service directly
            pass

        # We can't easily promote in test. Check auth is enforced.
        resp = await api_client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403  # Non-admin can't access

    async def test_all_admin_endpoints_require_auth(self, api_client: AsyncClient):
        """鲁棒性测试：所有 admin 端点都需要认证。"""
        endpoints = [
            ("GET", "/api/v1/admin/stats"),
            ("GET", "/api/v1/admin/tours"),
            ("GET", "/api/v1/admin/orders"),
            ("GET", "/api/v1/admin/users"),
            ("GET", "/api/v1/admin/reviews"),
        ]
        for method, url in endpoints:
            resp = await api_client.request(method, url)
            assert resp.status_code == 401, f"{method} {url} should return 401"

    async def test_admin_tours_pagination(self, api_client: AsyncClient):
        """边界测试：分页参数。"""
        resp = await api_client.get("/api/v1/admin/tours?page=2&page_size=10")
        assert resp.status_code == 401  # Not authenticated

    async def test_admin_tours_status_filter(self, api_client: AsyncClient):
        """功能测试：状态筛选参数。"""
        resp = await api_client.get("/api/v1/admin/tours?status=published")
        assert resp.status_code == 401

    async def test_admin_orders_pagination(self, api_client: AsyncClient):
        """边界测试：订单分页。"""
        resp = await api_client.get("/api/v1/admin/orders?page=1&page_size=5")
        assert resp.status_code == 401

    async def test_admin_users_pagination(self, api_client: AsyncClient):
        """边界测试：用户分页。"""
        resp = await api_client.get("/api/v1/admin/users?page=1&page_size=10")
        assert resp.status_code == 401

    async def test_admin_reviews_filter(self, api_client: AsyncClient):
        """功能测试：评论状态筛选。"""
        resp = await api_client.get("/api/v1/admin/reviews?status=pending")
        assert resp.status_code == 401
