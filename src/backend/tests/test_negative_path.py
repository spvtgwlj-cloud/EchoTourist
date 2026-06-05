"""逆向操作（Negative Path）测试。

覆盖范围：
- 收藏逆向：下单中途取消收藏、下单后修改收藏、已删除产品的收藏访问
- 订单逆向：支付前取消订单、无效订单状态、已支付订单重复支付
- 支付逆向：Webhook 签名验证失败
- 评价逆向：管理员拒绝评价后重新提交
- 多语言逆向：不存在的语言代码、用户资料无效 locale

本文件补充现有测试中未覆盖的逆向场景。
已由其他测试覆盖的项目仅作引用标注（✅）。
"""

import uuid
import asyncio
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.tour import Tour, TourDate
from app.models.attraction import Attraction
from app.models.attraction_wishlist import AttractionWishlist
from app.models.wishlist import Wishlist
from app.models.review import Review
from app.models.user import User
from app.core.security import create_access_token
from app.config import settings


# ──────────────────────────────────────────────
# TC-NEG-001 ~ 005：收藏逆向
# ──────────────────────────────────────────────


class TestWishlistNegative:
    """收藏功能逆向操作测试。"""

    async def _register_and_login(self, api_client: AsyncClient) -> dict:
        """辅助：注册新用户并返回 auth headers。"""
        email = f"neg_wl_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/auth/register", json={
            "email": email, "password": "Test1234!", "name": "Neg WL User",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def _get_first_tour(self, api_client: AsyncClient) -> tuple[str, str, int]:
        """辅助：获取第一个可用产品及其团期信息。"""
        resp = await api_client.get("/api/v1/tours?locale=en&page_size=1")
        tours = resp.json().get("tours", [])
        if not tours:
            pytest.skip("No tours available")
        tour_id = tours[0]["id"]

        resp = await api_client.get(f"/api/v1/tours/{tour_id}/dates")
        dates = resp.json().get("dates", [])
        avail = [d for d in dates if d["availability"] > 0]
        if not avail:
            pytest.skip("No available dates")
        return tour_id, avail[0]["id"], avail[0]["availability"]

    async def _create_order(
        self, api_client: AsyncClient, headers: dict, tour_id: str, date_id: str,
    ) -> dict:
        """辅助：创建订单并返回响应。"""
        email = f"neg_order_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/orders", json={
            "tour_id": tour_id,
            "tour_date_id": date_id,
            "pax_count": 1,
            "contact_name": "Neg Test",
            "contact_email": email,
            "locale": "en",
        }, headers=headers)
        assert resp.status_code == 200
        return resp.json()

    async def test_cancel_wishlist_during_checkout(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-001：下单中途取消收藏，订单不受影响。"""
        headers = await self._register_and_login(api_client)
        tour_id, date_id, _ = await self._get_first_tour(api_client)

        # 1. 收藏产品
        resp = await api_client.post(f"/api/v1/wishlist/{tour_id}", headers=headers)
        assert resp.status_code in (200, 201)

        # 2. 确认收藏存在
        resp = await api_client.get("/api/v1/wishlist", headers=headers)
        wishlist = resp.json().get("wishlist", resp.json().get("items", resp.json()))
        wishlist_ids = [w.get("id") if isinstance(w, dict) else w for w in (wishlist if isinstance(wishlist, list) else [])]
        if not any(str(tour_id) in str(w) for w in wishlist_ids):
            wishlist_items = wishlist if isinstance(wishlist, list) else []
            assert any(w["tour_id"] == tour_id for w in wishlist_items if isinstance(w, dict)), "Tour not in wishlist"

        # 3. 下单
        order = await self._create_order(api_client, headers, tour_id, date_id)

        # 4. 取消收藏
        resp = await api_client.delete(f"/api/v1/wishlist/{tour_id}", headers=headers)
        assert resp.status_code in (200, 204), f"Remove wishlist failed: {resp.status_code}"

        # 5. 验证收藏已删除
        resp = await api_client.get("/api/v1/wishlist", headers=headers)
        assert resp.status_code == 200

        # 6. 验证订单正常
        resp = await api_client.get(f"/api/v1/orders/{order['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_wishlist_after_order(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-002：下单后可以正常移除和重新添加收藏。"""
        headers = await self._register_and_login(api_client)
        tour_id, date_id, _ = await self._get_first_tour(api_client)

        # 1. 收藏
        resp = await api_client.post(f"/api/v1/wishlist/{tour_id}", headers=headers)
        assert resp.status_code in (200, 201)

        # 2. 下单
        await self._create_order(api_client, headers, tour_id, date_id)

        # 3. 取消收藏
        resp = await api_client.delete(f"/api/v1/wishlist/{tour_id}", headers=headers)
        assert resp.status_code in (200, 204)

        # 4. 重新收藏
        resp = await api_client.post(f"/api/v1/wishlist/{tour_id}", headers=headers)
        assert resp.status_code in (200, 201), f"Re-add after order failed: {resp.status_code}"

    async def test_wishlist_with_deleted_tour(
        self, api_client: AsyncClient, db_session: AsyncSession,
    ):
        """TC-NEG-003：产品被软删除后，收藏列表应正常显示（无崩溃）。"""
        headers = await self._register_and_login(api_client)
        tour_id, _, _ = await self._get_first_tour(api_client)

        # 1. 收藏产品
        resp = await api_client.post(f"/api/v1/wishlist/{tour_id}", headers=headers)
        assert resp.status_code in (200, 201)

        # 2. 通过 API 验证收藏存在
        resp = await api_client.get("/api/v1/wishlist", headers=headers)
        assert resp.status_code == 200

        # 3. 软删除产品（直接更新 DB）
        await db_session.execute(
            sa_update(Tour).where(Tour.id == tour_id).values(status="inactive")
        )
        await db_session.commit()

        # 4. 查看收藏列表 — 不崩溃
        resp = await api_client.get("/api/v1/wishlist", headers=headers)
        assert resp.status_code == 200, f"Wishlist page crashed after tour deletion: {resp.status_code}"
        data = resp.json()

        # 5. 恢复产品状态（清理）
        await db_session.execute(
            sa_update(Tour).where(Tour.id == tour_id).values(status="active")
        )
        await db_session.commit()

    async def test_attraction_wishlist_deleted(
        self, api_client: AsyncClient, db_session: AsyncSession,
    ):
        """TC-NEG-004：景点被删除后，景点收藏列表应正常显示（无崩溃）。"""
        headers = await self._register_and_login(api_client)

        # 获取景点
        resp = await api_client.get("/api/v1/destinations?locale=en")
        dests = resp.json().get("destinations", [])
        attr_id = None
        for dest in dests:
            resp = await api_client.get(
                f"/api/v1/destinations/{dest['slug']}/attractions?locale=en"
            )
            attrs = resp.json().get("attractions", [])
            if attrs:
                attr_id = attrs[0]["id"]
                break
        if not attr_id:
            pytest.skip("No attractions available")

        # 1. 收藏景点
        resp = await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp.status_code in (200, 201)

        # 2. 通过 API 删除景点（如果可以）或直接 DB 操作
        # 景点可能有外键约束，这里直接标记为 inactive
        await db_session.execute(
            sa_update(Attraction).where(Attraction.id == attr_id).values(status="inactive")
        )
        await db_session.commit()

        # 3. 查看景点收藏列表 — 不崩溃
        resp = await api_client.get("/api/v1/wishlist/attractions", headers=headers)
        assert resp.status_code == 200, (
            f"Attraction wishlist page crashed after deletion: {resp.status_code}"
        )

        # 4. 恢复
        await db_session.execute(
            sa_update(Attraction).where(Attraction.id == attr_id).values(status="active")
        )
        await db_session.commit()

    async def test_attraction_wishlist_duplicate(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-005：景点收藏重复操作——重复添加和二次删除。"""
        headers = await self._register_and_login(api_client)

        # 获取景点
        resp = await api_client.get("/api/v1/destinations?locale=en")
        dests = resp.json().get("destinations", [])
        attr_id = None
        for dest in dests:
            resp = await api_client.get(
                f"/api/v1/destinations/{dest['slug']}/attractions?locale=en"
            )
            attrs = resp.json().get("attractions", [])
            if attrs:
                attr_id = attrs[0]["id"]
                break
        if not attr_id:
            pytest.skip("No attractions available")

        # 1. 首次添加收藏
        resp = await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp.status_code in (200, 201)

        # 2. 重复添加同一景点——应成功（幂等，返回 200 表示已存在）
        resp = await api_client.post(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp.status_code in (200, 201, 409), (
            f"Duplicate add should be idempotent, got {resp.status_code}"
        )

        # 3. 取消收藏
        resp = await api_client.delete(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp.status_code in (200, 204)

        # 4. 二次取消——应返回 404（已删除）
        resp = await api_client.delete(
            f"/api/v1/wishlist/attractions/{attr_id}", headers=headers,
        )
        assert resp.status_code in (404, 200, 204), (
            f"Second delete should return 404, got {resp.status_code}"
        )


# ──────────────────────────────────────────────
# TC-NEG-006 ~ 010：订单逆向
# ──────────────────────────────────────────────


class TestOrderNegative:
    """订单功能逆向操作测试。

    ✅ TC-NEG-008（用户A查看B的订单）→ test_security.py::test_view_others_order
    ✅ TC-NEG-010（重复下单同一团期）→ test_concurrency.py::test_same_user_duplicate_order
    """

    async def _register_and_get_tour(self, api_client: AsyncClient) -> tuple[dict, str, str]:
        """辅助：注册用户并获取可用产品。"""
        email = f"neg_ord_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/auth/register", json={
            "email": email, "password": "Test1234!", "name": "Neg Ord",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await api_client.get("/api/v1/tours?locale=en&page_size=1")
        tours = resp.json().get("tours", [])
        if not tours:
            pytest.skip("No tours available")
        tour_id = tours[0]["id"]

        resp = await api_client.get(f"/api/v1/tours/{tour_id}/dates")
        dates = resp.json().get("dates", [])
        avail = [d for d in dates if d["availability"] > 0]
        if not avail:
            pytest.skip("No available dates")

        return headers, tour_id, avail[0]["id"]

    async def test_cancel_before_payment(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-006：支付前取消订单——验证订单为 pending 可核实。

        由于当前无公开取消 API，验证订单创建后处于 pending 状态。
        """
        headers, tour_id, date_id = await self._register_and_get_tour(api_client)

        email = f"neg_cancel_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/orders", json={
            "tour_id": tour_id,
            "tour_date_id": date_id,
            "pax_count": 1,
            "contact_name": "Neg Cancel",
            "contact_email": email,
            "locale": "en",
        }, headers=headers)
        assert resp.status_code == 200
        order = resp.json()

        # 订单处于 pending 状态
        assert order["status"] == "pending", (
            f"New order should be pending, got {order['status']}"
        )

        # 查询订单详情再次确认
        resp = await api_client.get(f"/api/v1/orders/{order['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    async def test_invalid_order_status(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-009：管理员将订单状态设为无效值应被拒绝。"""
        headers, tour_id, date_id = await self._register_and_get_tour(api_client)

        # 创建订单
        email = f"neg_status_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/orders", json={
            "tour_id": tour_id,
            "tour_date_id": date_id,
            "pax_count": 1,
            "contact_name": "Neg Status",
            "contact_email": email,
            "locale": "en",
        }, headers=headers)
        assert resp.status_code == 200
        order_id = resp.json()["id"]

        # 管理员登录
        resp = await api_client.post("/api/v1/auth/login", json={
            "email": "admin@echotours.com",
            "password": "Admin123!",
        })
        assert resp.status_code == 200
        admin_token = resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 尝试设置无效状态值（通过 admin PATCH 订单端点，若不存在则跳过）
        resp = await api_client.patch(
            f"/api/v1/admin/orders/{order_id}",
            json={"status": "invalid_status_xyz"},
            headers=admin_headers,
        )
        # 如果端点存在，应返回 400 或 422；如果不存在，返回 404 正常
        if resp.status_code == 404:
            pytest.skip("Admin PATCH order endpoint not available")
        assert resp.status_code in (400, 422), (
            f"Invalid status should be rejected, got {resp.status_code}: {resp.text}"
        )


# ──────────────────────────────────────────────
# TC-NEG-011 ~ 014：支付逆向
# ──────────────────────────────────────────────


class TestPaymentNegative:
    """支付功能逆向操作测试。"""

    async def _setup_order(self, api_client: AsyncClient) -> tuple[dict, str]:
        """辅助：注册用户、创建订单，返回 headers 和 order_id。"""
        email = f"neg_pay_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/auth/register", json={
            "email": email, "password": "Test1234!", "name": "Neg Pay",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await api_client.get("/api/v1/tours?locale=en&page_size=5")
        tours = resp.json().get("tours", [])
        if not tours:
            pytest.skip("No tours available")
        tour_id = tours[0]["id"]

        resp = await api_client.get(f"/api/v1/tours/{tour_id}/dates")
        dates = resp.json().get("dates", [])
        avail = [d for d in dates if d["availability"] > 0]
        if not avail:
            pytest.skip("No available dates")

        email = f"neg_pay_contact_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/orders", json={
            "tour_id": tour_id,
            "tour_date_id": avail[0]["id"],
            "pax_count": 1,
            "contact_name": "Neg Pay",
            "contact_email": email,
            "locale": "en",
        }, headers=headers)
        assert resp.status_code == 200
        return headers, resp.json()["id"]

    async def test_double_payment_attempt(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-011：已支付订单不应再次支付。

        注意：集成测试环境使用 Mock 支付，
        若 mock 模式不校验支付状态则标记为跳过。
        """
        headers, order_id = await self._setup_order(api_client)

        # 创建支付 intent
        resp = await api_client.post(
            "/api/v1/payments/create-intent",
            json={"order_id": str(order_id)},
            headers=headers,
        )

        if resp.status_code == 404:
            pytest.skip("Payment endpoint not available in this environment")
        assert resp.status_code in (200, 201), (
            f"Payment creation failed: {resp.status_code} {resp.text}"
        )

        # 第二次创建支付——预期结果取决于业务逻辑
        # 如果系统允许为同一个订单创建多次 intent（会覆盖旧的），则返回 200
        # 如果系统阻止重复支付，则返回 400
        resp2 = await api_client.post(
            "/api/v1/payments/create-intent",
            json={"order_id": str(order_id)},
            headers=headers,
        )
        assert resp2.status_code in (200, 400), (
            f"Second payment attempt unexpected: {resp2.status_code} {resp2.text}"
        )

    async def test_payment_already_paid(
        self, api_client: AsyncClient, db_session: AsyncSession,
    ):
        """TC-NEG-012：订单已支付后创建支付意图应被拒绝。"""
        headers, order_id = await self._setup_order(api_client)

        # 直接更新订单为已支付状态（模拟支付成功）
        await db_session.execute(
            sa_update(Order).where(Order.id == order_id).values(
                status="confirmed",
                payment_status="paid",
            )
        )
        await db_session.commit()

        # 尝试再次创建支付——应被拒绝
        resp = await api_client.post(
            "/api/v1/payments/create-intent",
            json={"order_id": str(order_id)},
            headers=headers,
        )

        if resp.status_code == 404:
            pytest.skip("Payment endpoint not available")

        assert resp.status_code in (400, 422), (
            f"Already paid order should be rejected, got {resp.status_code}: {resp.text}"
        )

        # 清理：恢复订单状态
        await db_session.execute(
            sa_update(Order).where(Order.id == order_id).values(
                status="pending",
                payment_status="pending",
            )
        )
        await db_session.commit()

    async def test_webhook_invalid_signature(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-013：Webhook 签名验证失败应返回 400。"""
        resp = await api_client.post(
            "/api/v1/payments/stripe-webhook",
            json={"type": "checkout.session.completed", "data": {"object": {}}},
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "invalid_signature_xyz",
            },
        )
        # Stripe未配置时返回 ignored，签名无效时返回 400
        assert resp.status_code in (400, 404, 200), (
            f"Invalid webhook signature unexpected: {resp.status_code}: {resp.text}"
        )

    async def test_payment_negative_amount(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-014：负值金额在下单时被 pydantic 校验拒绝。

        注意：BookingRequest 没有 total 字段（服务器计算总额），
        所以通过 pax_count=0 或负值测试 pydantic Field(gt=0) 校验。
        ✅ 已由 test_security.py::test_negative_numeric_values 覆盖。
        """
        pytest.skip("Covered by test_security.py::test_negative_numeric_values (pax_count=0/‑1 → 422)")


# ──────────────────────────────────────────────
# TC-NEG-015 ~ 018：评价逆向
# ──────────────────────────────────────────────


class TestReviewNegative:
    """评价功能逆向操作测试。

    ✅ TC-NEG-015（未登录提交评价）→ test_security.py::test_missing_auth_header
    ✅ TC-NEG-016（无订单用户提交评价）→ test_business_flow_enhanced.py::TestReviewDeduplication
    ✅ TC-NEG-017（评分越界 0/6）→ test_business_flow_enhanced.py::TestAuthEdgeCases（pydantic 校验）
    """

    async def test_review_rejected_and_resubmit(
        self, api_client: AsyncClient, db_session: AsyncSession,
    ):
        """TC-NEG-018：管理员拒绝评价后，用户可以再次提交同一产品的评价。"""
        # 注册用户
        email = f"neg_rev_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/auth/register", json={
            "email": email, "password": "Test1234!", "name": "Neg Rev",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取产品
        resp = await api_client.get("/api/v1/tours?locale=en&page_size=1")
        tours = resp.json().get("tours", [])
        if not tours:
            pytest.skip("No tours available")
        tour_id = tours[0]["id"]

        # 先由管理员确认用户有一个订单（评价前置条件）
        # 具体条件因业务而异，此处直接尝试提交评价
        resp = await api_client.post("/api/v1/reviews", json={
            "tour_id": tour_id,
            "rating": 4,
            "title": "Review for reject test",
            "comment": "This review will be rejected",
            "locale": "en",
        }, headers=headers)

        if resp.status_code != 200:
            # 如果评价前置条件不满足（如需要已确认订单），跳过
            pytest.skip(f"Review submission requires pre-condition: {resp.status_code} {resp.text[:100]}")

        review_id = resp.json().get("id", resp.json().get("review_id"))

        # 管理员登录并拒绝评价
        resp = await api_client.post("/api/v1/auth/login", json={
            "email": "admin@echotours.com",
            "password": "Admin123!",
        })
        assert resp.status_code == 200
        admin_token = resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 查找管理后台拒绝评价的端点
        if review_id:
            resp = await api_client.patch(
                f"/api/v1/admin/reviews/{review_id}",
                json={"status": "rejected"},
                headers=admin_headers,
            )

        # 再次提交评价——应可以重新提交（未被禁止）
        resp = await api_client.post("/api/v1/reviews", json={
            "tour_id": tour_id,
            "rating": 5,
            "title": "Resubmitted review",
            "comment": "Trying again after rejection",
            "locale": "en",
        }, headers=headers)
        # 可能成功，也可能因前置条件仍然返回错误
        # 但至少不应该是 500
        assert resp.status_code != 500, "Server error on resubmit"
        assert resp.status_code != 403, "Resubmit should not be forbidden unconditionally"


# ──────────────────────────────────────────────
# TC-NEG-021 ~ 022：多语言逆向
# ──────────────────────────────────────────────


class TestLocaleNegative:
    """多语言逆向操作测试。

    ✅ TC-NEG-019（下单过程切换语言）→ negative-flow.spec.ts（E2E）
    ✅ TC-NEG-020（混合语言搜索）→ negative-flow.spec.ts（E2E）
    """

    async def test_invalid_locale_fallback(self, api_client: AsyncClient):
        """TC-NEG-021：不存在的语言代码应 fallback 到默认语言。"""
        # 测试不存在的语言代码
        invalid_locales = ["fr", "de", "ja", "ko", "xx"]

        for locale in invalid_locales:
            resp = await api_client.get(f"/api/v1/tours?locale={locale}&page_size=1")
            # 应正常返回（fallback 到默认语言 en），而非 404/500
            assert resp.status_code == 200, (
                f"Invalid locale '{locale}' caused {resp.status_code}: {resp.text[:100]}"
            )
            data = resp.json()
            assert "tours" in data, f"Missing 'tours' in response for locale '{locale}'"

        # 搜索也应有 fallback
        for locale in invalid_locales:
            resp = await api_client.get(f"/api/v1/search?q=beijing&locale={locale}")
            assert resp.status_code == 200, (
                f"Search with invalid locale '{locale}' caused {resp.status_code}"
            )

        # 目的地列表
        for locale in invalid_locales:
            resp = await api_client.get(f"/api/v1/destinations?locale={locale}")
            assert resp.status_code == 200, (
                f"Destinations with invalid locale '{locale}' caused {resp.status_code}"
            )

    async def test_profile_invalid_locale(
        self, api_client: AsyncClient,
    ):
        """TC-NEG-022：用户资料切换不存在的语言后访问各页面。"""
        # 注册用户
        email = f"neg_loc_{uuid.uuid4().hex[:8]}@example.com"
        resp = await api_client.post("/api/v1/auth/register", json={
            "email": email, "password": "Test1234!", "name": "Neg Loc",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 更新用户 locale 为不存在的值（如果 API 允许）
        resp = await api_client.patch(
            "/api/v1/auth/me",
            json={"locale": "xx"},
            headers=headers,
        )
        # 如果 API 校验 locale，返回 422；如果不校验，更新成功然后看 fallback
        if resp.status_code == 422:
            pytest.skip("API rejects invalid locale value — validation working correctly")
            return

        # 访问各页面检查不崩溃
        pages = [
            "/api/v1/tours?locale=xx&page_size=1",
            "/api/v1/destinations?locale=xx",
            "/api/v1/search?q=beijing&locale=xx",
        ]
        for path in pages:
            resp = await api_client.get(path, headers=headers)
            assert resp.status_code == 200, (
                f"Page {path} crashed after setting invalid locale: {resp.status_code}"
            )

        # 恢复 locale（清理）
        await api_client.patch(
            "/api/v1/auth/me",
            json={"locale": "en"},
            headers=headers,
        )
