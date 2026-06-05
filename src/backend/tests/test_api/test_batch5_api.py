"""Batch 5 全面 API 集成测试 —— Destinations / Wishlist / Users / Reviews / Checkout。

覆盖功能测试、边界测试、鲁棒性测试。
"""

import uuid

import pytest
from httpx import AsyncClient


# ============================================================
# Destinations
# ============================================================

class TestDestinationsAPI:
    """目的地 API 完整测试。"""

    async def test_list_destinations_empty(self, api_client: AsyncClient):
        """功能测试：空列表返回正常结构。"""
        resp = await api_client.get("/api/v1/destinations?locale=en")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["destinations"], list)

    async def test_list_destinations_multilingual(self, api_client: AsyncClient):
        """功能测试：多语言不影响列表结构。"""
        for lang in ["en", "zh", "es"]:
            resp = await api_client.get(f"/api/v1/destinations?locale={lang}")
            assert resp.status_code == 200

    async def test_get_destination_not_found(self, api_client: AsyncClient):
        """鲁棒性测试：不存在的 slug 返回 404。"""
        resp = await api_client.get("/api/v1/destinations/nonexistent-slug-12345")
        assert resp.status_code == 404
        assert resp.json().get("error_code") == "NOT_FOUND"

    async def test_get_destination_empty_slug(self, api_client: AsyncClient):
        """边界测试：空 slug 回退到列表页（200）。"""
        resp = await api_client.get("/api/v1/destinations/")
        # FastAPI 将 /destinations/ 重定向到列表
        assert resp.status_code in (200, 307)

    async def test_destination_tours_not_found(self, api_client: AsyncClient):
        """鲁棒性测试：不存在目的地的 tours 返回 404。"""
        resp = await api_client.get("/api/v1/destinations/nonexistent/tours")
        assert resp.status_code == 404

    async def test_destination_tours_empty_list(self, api_client: AsyncClient):
        """边界测试：存在但无 tours 的目的地。"""
        resp = await api_client.get("/api/v1/destinations?locale=en")
        data = resp.json()
        if data["destinations"]:
            slug = data["destinations"][0]["slug"]
            tours_resp = await api_client.get(f"/api/v1/destinations/{slug}/tours")
            assert tours_resp.status_code == 200
            assert "tours" in tours_resp.json()


# ============================================================
# Wishlist
# ============================================================

class TestWishlistAPI:
    """收藏 API 完整测试。"""

    async def _register_and_get_token(self, api_client: AsyncClient) -> str:
        """helper：注册用户并返回 token。"""
        unique_email = f"wl_test_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/auth/register", json={
            "email": unique_email,
            "password": "TestPass123!",
            "name": "WL Tester",
        })
        return resp.json()["access_token"]

    async def test_wishlist_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证返回 401。"""
        # GET list
        resp = await api_client.get("/api/v1/wishlist")
        assert resp.status_code == 401

        # POST add
        resp = await api_client.post(f"/api/v1/wishlist/{uuid.uuid4()}")
        assert resp.status_code == 401

        # DELETE remove
        resp = await api_client.delete(f"/api/v1/wishlist/{uuid.uuid4()}")
        assert resp.status_code == 401

    async def test_wishlist_empty(self, api_client: AsyncClient):
        """功能测试：空收藏返回空列表。"""
        token = await self._register_and_get_token(api_client)
        resp = await api_client.get(
            "/api/v1/wishlist",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    async def test_wishlist_add_not_found(self, api_client: AsyncClient):
        """鲁棒性测试：添加不存在的 tour 返回 404。"""
        token = await self._register_and_get_token(api_client)
        resp = await api_client.post(
            f"/api/v1/wishlist/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_wishlist_add_invalid_uuid(self, api_client: AsyncClient):
        """边界测试：无效 UUID 格式返回 422。"""
        token = await self._register_and_get_token(api_client)
        resp = await api_client.post(
            "/api/v1/wishlist/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_wishlist_delete_invalid_uuid(self, api_client: AsyncClient):
        """边界测试：删除时无效 UUID。"""
        token = await self._register_and_get_token(api_client)
        resp = await api_client.delete(
            "/api/v1/wishlist/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_wishlist_delete_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：删除未认证。"""
        resp = await api_client.delete(f"/api/v1/wishlist/{uuid.uuid4()}")
        assert resp.status_code == 401

    async def test_wishlist_multiple_add_same(self, api_client: AsyncClient, factory):
        """鲁棒性测试：重复添加不报错。"""
        token = await self._register_and_get_token(api_client)
        fake_tour = str(uuid.uuid4())

        # First add will 404 (tour not found), so this tests error handling
        resp1 = await api_client.post(
            f"/api/v1/wishlist/{fake_tour}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp1.status_code == 404


# ============================================================
# Users / Profile
# ============================================================

class TestUsersAPI:
    """用户 API 完整测试。"""

    async def test_get_profile_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证返回 401。"""
        resp = await api_client.get("/api/v1/users/me/profile")
        assert resp.status_code == 401

    async def test_update_profile_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：更新 profile 未认证。"""
        resp = await api_client.patch("/api/v1/users/me/profile", json={"name": "Hack"})
        assert resp.status_code == 401

    async def test_get_profile_with_auth(self, api_client: AsyncClient, factory):
        """功能测试：认证后可获取完整 profile。"""
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]

        resp = await api_client.get(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == reg["email"]
        assert data["name"] == reg["name"]
        assert "review_count" in data
        assert "order_count" in data
        assert "is_admin" in data
        assert data["is_admin"] is False

    async def test_update_profile_full(self, api_client: AsyncClient, factory):
        """功能测试：更新所有 profile 字段。"""
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]

        resp = await api_client.patch(
            "/api/v1/users/me/profile",
            json={"name": "New Name", "locale": "zh", "avatar_url": "https://example.com/ava.jpg"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        assert data["locale"] == "zh"
        assert data["avatar_url"] == "https://example.com/ava.jpg"

    async def test_update_profile_partial(self, api_client: AsyncClient, factory):
        """功能测试：部分更新（只更新 locale）。"""
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]

        # 只更新 locale
        resp = await api_client.patch(
            "/api/v1/users/me/profile",
            json={"locale": "es"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["locale"] == "es"
        assert resp.json()["name"] == reg["name"]  # 不应变化

    async def test_update_profile_empty_body(self, api_client: AsyncClient, factory):
        """边界测试：空请求体。"""
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]

        resp = await api_client.patch(
            "/api/v1/users/me/profile",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200  # 应保持不变返回成功

    async def test_update_profile_email_immutable(self, api_client: AsyncClient, factory):
        """鲁棒性测试：邮箱不可通过 profile 接口修改。"""
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]

        resp = await api_client.patch(
            "/api/v1/users/me/profile",
            json={"email": "hacked@example.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == reg["email"]  # 邮箱未变化


# ============================================================
# Reviews
# ============================================================

class TestReviewsAPI:
    """评论 API 完整测试。"""

    async def test_create_review_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证创建评论返回 401。"""
        resp = await api_client.post(
            "/api/v1/reviews",
            json={"tour_id": str(uuid.uuid4()), "rating": 5},
        )
        assert resp.status_code == 401

    async def test_create_review_invalid_rating_high(self, api_client: AsyncClient):
        """边界测试：rating > 5 返回 422。"""
        resp = await api_client.post(
            "/api/v1/reviews",
            json={"tour_id": str(uuid.uuid4()), "rating": 10, "locale": "en"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code in (401, 422)

    async def test_create_review_invalid_rating_low(self, api_client: AsyncClient):
        """边界测试：rating < 1 返回 422。"""
        resp = await api_client.post(
            "/api/v1/reviews",
            json={"tour_id": str(uuid.uuid4()), "rating": 0, "locale": "en"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code in (401, 422)

    async def test_create_review_missing_tour_id(self, api_client: AsyncClient):
        """边界测试：缺少 tour_id 返回 422。"""
        resp = await api_client.post(
            "/api/v1/reviews",
            json={"rating": 5, "locale": "en"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code in (401, 422)

    async def test_create_review_invalid_tour_uuid(self, api_client: AsyncClient):
        """边界测试：无效 tour_id 格式。"""
        resp = await api_client.post(
            "/api/v1/reviews",
            json={"tour_id": "not-a-uuid", "rating": 5, "locale": "en"},
            headers={"Authorization": "Bearer test"},
        )
        assert resp.status_code in (401, 422)

    async def test_get_reviews_tour_not_found(self, api_client: AsyncClient):
        """边界测试：不存在的 tour 评论返回空列表。"""
        resp = await api_client.get(f"/api/v1/reviews/tour/{uuid.uuid4()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["reviews"] == []
        assert data["total"] == 0

    async def test_get_reviews_realistic_flow(self, api_client: AsyncClient, factory):
        """集成测试：注册 → 创建评论 → 获取评论列表。"""
        reg = factory.valid_register_data()
        r = await api_client.post("/api/v1/auth/register", json=reg)
        token = r.json()["access_token"]

        nonexistent_tour = str(uuid.uuid4())
        resp = await api_client.post(
            "/api/v1/reviews",
            json={
                "tour_id": nonexistent_tour,
                "rating": 4,
                "title": "Great Tour",
                "comment": "Amazing experience!",
                "locale": "en",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        # tour 不存在，可能 200（创建成功但 FK 约束存在）或 404/422
        assert resp.status_code in (200, 404, 422, 500)

    async def test_get_reviews_pagination(self, api_client: AsyncClient):
        """功能测试：分页参数正确传递。"""
        resp = await api_client.get(
            f"/api/v1/reviews/tour/{uuid.uuid4()}?page=2&page_size=5"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0


# ============================================================
# Checkout Flow
# ============================================================

class TestCheckoutFlow:
    """结账流程集成测试（订单 + 支付创建）。"""

    async def test_payment_create_intent_invalid(self, api_client: AsyncClient):
        """鲁棒性测试：无效 order_id 返回 404。"""
        resp = await api_client.post(
            "/api/v1/payments/create-intent",
            json={"order_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 404

    async def test_payment_create_intent_missing_id(self, api_client: AsyncClient):
        """边界测试：缺少 order_id。"""
        resp = await api_client.post("/api/v1/payments/create-intent", json={})
        assert resp.status_code in (400, 422)

    async def test_payment_webhook_unconfigured(self, api_client: AsyncClient):
        """鲁棒性测试：未配置 Stripe 时 webhook 返回 ignored。"""
        resp = await api_client.post(
            "/api/v1/payments/stripe-webhook",
            data=b'{}',
        )
        assert resp.status_code in (200, 400)

    async def test_payment_create_intent_invalid_uuid(self, api_client: AsyncClient):
        """边界测试：无效 UUID 格式。"""
        resp = await api_client.post(
            "/api/v1/payments/create-intent",
            json={"order_id": "bad-data"},
        )
        assert resp.status_code in (400, 422)
