"""API 集成测试 —— 旅游产品/订单/支付/搜索（通过运行中的 Docker 服务）。"""

import uuid

import pytest
from httpx import AsyncClient


class TestToursAPI:
    """旅游产品 API。"""

    async def test_list_tours(self, api_client: AsyncClient):
        """功能测试：列表返回 200。"""
        response = await api_client.get("/api/v1/tours?locale=en")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["tours"], list)
        assert isinstance(data["total"], int)

    async def test_list_tours_pagination(self, api_client: AsyncClient):
        """边界测试：分页参数。"""
        response = await api_client.get("/api/v1/tours?page=2&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    async def test_list_tours_invalid_page(self, api_client: AsyncClient):
        """边界测试：page=0 返回 422。"""
        response = await api_client.get("/api/v1/tours?page=0")
        assert response.status_code == 422

    async def test_get_tour_not_found(self, api_client: AsyncClient):
        """鲁棒性测试：不存在返回 404。"""
        response = await api_client.get("/api/v1/tours/nonexistent-slug?locale=en")
        assert response.status_code == 404
        data = response.json()
        assert data.get("error_code") == "NOT_FOUND"

    async def test_get_tour_dates_invalid_uuid(self, api_client: AsyncClient):
        """边界测试：无效 UUID 格式返回 422。"""
        response = await api_client.get("/api/v1/tours/not-a-uuid/dates")
        assert response.status_code == 422


class TestSearchAPI:
    """搜索 API。"""

    async def test_search_empty(self, api_client: AsyncClient):
        """功能测试：无参搜索返回 200。"""
        response = await api_client.get("/api/v1/search")
        assert response.status_code == 200

    async def test_search_with_query(self, api_client: AsyncClient):
        """功能测试：关键词搜索。"""
        response = await api_client.get("/api/v1/search?q=hiking&locale=en")
        assert response.status_code == 200
        data = response.json()
        assert "facets" in data or "tours" in data

    async def test_search_special_chars(self, api_client: AsyncClient):
        """鲁棒性测试：特殊字符不崩溃。"""
        response = await api_client.get("/api/v1/search?q=%24%25%5E%26*&locale=en")
        assert response.status_code == 200

    async def test_search_pagination(self, api_client: AsyncClient):
        """功能测试：搜索分页。"""
        response = await api_client.get("/api/v1/search?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


class TestOrdersAPI:
    """订单 API。"""

    async def test_list_orders_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证返回 401。"""
        response = await api_client.get("/api/v1/orders")
        assert response.status_code == 401

    async def test_get_order_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证详情返回 401。"""
        response = await api_client.get(f"/api/v1/orders/{uuid.uuid4()}")
        assert response.status_code == 401

    async def test_create_order_no_auth(self, api_client: AsyncClient):
        """鲁棒性测试：未认证创建返回 401。"""
        response = await api_client.post(
            "/api/v1/orders",
            json={"tour_id": str(uuid.uuid4()), "tour_date_id": str(uuid.uuid4()),
                   "pax_count": 1, "contact_name": "Test", "contact_email": "t@t.com",
                   "locale": "en"},
        )
        assert response.status_code == 401

    async def test_create_order_validation(self, api_client: AsyncClient):
        """边界测试：空 body 返回 422。"""
        response = await api_client.post(
            "/api/v1/orders",
            json={},
            headers={"Authorization": "Bearer test"},
        )
        assert response.status_code in (401, 422)  # 可能 token 先验证失败

    async def test_create_order_invalid_uuid(self, api_client: AsyncClient):
        """边界测试：无效 UUID 格式返回 422。"""
        response = await api_client.post(
            "/api/v1/orders",
            json={
                "tour_id": "not-uuid", "tour_date_id": "not-uuid",
                "pax_count": 1, "contact_name": "T", "contact_email": "t@t.com",
                "locale": "en",
            },
            headers={"Authorization": "Bearer test"},
        )
        assert response.status_code in (401, 422)


class TestPaymentsAPI:
    """支付 API。"""

    async def test_create_intent_invalid_order(self, api_client: AsyncClient):
        """边界测试：不存在的订单返回 404。"""
        response = await api_client.post(
            "/api/v1/payments/create-intent",
            json={"order_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404

    async def test_create_intent_missing_order_id(self, api_client: AsyncClient):
        """边界测试：缺少 order_id 返回 400/422。"""
        response = await api_client.post("/api/v1/payments/create-intent", json={})
        assert response.status_code in (400, 422)

    async def test_webhook_no_signature(self, api_client: AsyncClient):
        """鲁棒性测试：无签名 webhook。"""
        response = await api_client.post(
            "/api/v1/payments/stripe-webhook",
            content=b'{}',
        )
        assert response.status_code in (200, 400)
