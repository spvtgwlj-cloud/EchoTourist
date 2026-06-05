"""景点收藏 API 集成测试。

覆盖范围：
- 添加景点收藏（正常/重复/无效ID）
- 移除景点收藏（正常/重复）
- 查看景点收藏列表
- 认证校验（未登录/无效token）
- 跨用户隔离
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.security import hash_password, create_access_token


class TestAttractionWishlistAPI:
    """景点收藏 API 集成测试。"""

    async def _create_user_and_token(
        self, api_client: AsyncClient
    ) -> tuple[str, dict]:
        """辅助：注册用户并返回 token + headers。"""
        email = f"aw_test_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPass123!",
            "name": "AW Test User",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        return token, {"Authorization": f"Bearer {token}"}

    async def _get_ready_attraction_id(self, api_client: AsyncClient) -> str:
        """辅助：从种子数据中获取一个可用景点 ID。"""
        # 获取目的地列表
        resp = await api_client.get("/api/v1/destinations?locale=en")
        assert resp.status_code == 200
        dests = resp.json().get("destinations", [])
        if not dests:
            pytest.skip("No destinations in seed data")

        # 获取第一个目的地的景点
        for dest in dests:
            resp = await api_client.get(
                f"/api/v1/destinations/{dest['slug']}/attractions?locale=en"
            )
            if resp.status_code == 200:
                attrs = resp.json().get("attractions", [])
                if attrs:
                    return attrs[0]["id"]
        pytest.skip("No attractions in seed data")

    # ── 正向流程 ─────────────────────────────────────────────

    async def test_add_attraction_to_wishlist(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-001：正常添加景点收藏。"""
        token, headers = await self._create_user_and_token(api_client)
        attr_id = await self._get_ready_attraction_id(api_client)

        resp = await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "id" in data

    async def test_get_attraction_wishlist(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-002：查看景点收藏列表。"""
        token, headers = await self._create_user_and_token(api_client)
        attr_id = await self._get_ready_attraction_id(api_client)

        # 先添加一个收藏
        await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )

        resp = await api_client.get("/api/v1/wishlist/attractions", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert data["items"][0]["attraction_id"] == attr_id
        assert data["items"][0]["attraction_name"] is not None

    async def test_remove_attraction_from_wishlist(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-003：移除景点收藏。"""
        token, headers = await self._create_user_and_token(api_client)
        attr_id = await self._get_ready_attraction_id(api_client)

        # 先添加
        await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )

        # 再移除
        resp = await api_client.delete(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # 验证已从列表中消失
        resp = await api_client.get("/api/v1/wishlist/attractions", headers=headers)
        assert len(resp.json()["items"]) == 0

    # ── 逆向操作 ─────────────────────────────────────────────

    async def test_duplicate_add_returns_ok(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-004：重复添加景点收藏返回 status=ok。"""
        token, headers = await self._create_user_and_token(api_client)
        attr_id = await self._get_ready_attraction_id(api_client)

        resp1 = await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp1.status_code == 200

        resp2 = await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "ok"

    async def test_remove_nonexistent_returns_not_found(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-005：移除不存在的收藏返回 not_found。"""
        token, headers = await self._create_user_and_token(api_client)

        resp = await api_client.delete(
            f"/api/v1/wishlist/attractions/{uuid.uuid4()}", headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "not_found"

    async def test_add_invalid_uuid_returns_422(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-006：无效 UUID 格式返回 422。"""
        token, headers = await self._create_user_and_token(api_client)

        resp = await api_client.post(
            "/api/v1/wishlist/attractions/not-a-uuid", headers=headers,
        )
        assert resp.status_code in (422, 400)

    # ── 权限校验 ─────────────────────────────────────────────

    async def test_unauthenticated_cannot_add(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-007：未登录用户无法添加收藏。"""
        resp = await api_client.post(
            f"/api/v1/wishlist/attractions/{uuid.uuid4()}",
        )
        assert resp.status_code in (401, 403)

    async def test_unauthenticated_cannot_view(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-008：未登录用户无法查看收藏列表。"""
        resp = await api_client.get("/api/v1/wishlist/attractions")
        assert resp.status_code in (401, 403)

    async def test_invalid_token_returns_401(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-009：无效 token 访问返回 401。"""
        resp = await api_client.get(
            "/api/v1/wishlist/attractions",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    # ── 数据隔离 ─────────────────────────────────────────────

    async def test_cross_user_isolation(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-010：不同用户的景点收藏互不干扰。"""
        attr_id = await self._get_ready_attraction_id(api_client)

        # 用户A添加收藏
        token_a, headers_a = await self._create_user_and_token(api_client)
        await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers_a,
        )

        # 用户B查看列表——应为空
        token_b, headers_b = await self._create_user_and_token(api_client)
        resp = await api_client.get("/api/v1/wishlist/attractions", headers=headers_b)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 0

        # 用户A的收藏仍存在
        resp = await api_client.get("/api/v1/wishlist/attractions", headers=headers_a)
        assert len(resp.json()["items"]) == 1

    # ── 景点收藏与产品收藏独立 ───────────────────────────────

    async def test_wishlist_types_independent(
        self, api_client: AsyncClient,
    ):
        """TC-WISH-ATTR-API-011：景点收藏与产品收藏是独立的命名空间。"""
        token, headers = await self._create_user_and_token(api_client)
        attr_id = await self._get_ready_attraction_id(api_client)

        # 添加景点收藏
        await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )

        # 产品收藏列表应为空（或至少与景点收藏不同）
        resp = await api_client.get("/api/v1/wishlist", headers=headers)
        assert resp.status_code == 200
        tour_wl = resp.json().get("items", [])

        # 景点收藏列表应有 1 项
        resp = await api_client.get("/api/v1/wishlist/attractions", headers=headers)
        attr_wl = resp.json().get("items", [])
        assert len(attr_wl) == 1

        # 验证是两个不同的接口
        assert len(attr_wl) != len(tour_wl) or (
            attr_wl[0]["attraction_id"] != tour_wl[0].get("tour_id")
            if tour_wl else True
        )
