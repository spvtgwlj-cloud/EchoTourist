"""自定制旅程 API 集成测试（含 Session 16 custom_destination 支持）。

测试策略：
- API 集成测试通过 httpx 请求运行中的 Docker 后端服务
- 使用 _admin_engine 模式直接操作数据库获取 seed 数据引用
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings


@pytest.fixture
def _direct_engine():
    """独立引擎用于直接查询 seed 数据。"""
    engine = create_async_engine(settings.database_url, echo=False, pool_size=1)
    yield engine
    # 不需要 await engine.dispose() — 这是一个 sync fixture
    # 引擎在测试结束时自动释放


async def _register_user(
    api_client: AsyncClient, email: str | None = None
) -> str:
    """注册用户并返回 JWT。"""
    if not email:
        email = f"ctuser_{uuid.uuid4().hex[:8]}@example.com"
    resp = await api_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "name": "Custom Tour Tester",
    })
    assert resp.status_code in (200, 201), f"Registration failed: {resp.text}"
    return resp.json()["access_token"]


async def _get_first_destination_id(_direct_engine) -> uuid.UUID | None:
    """获取 seed 数据中第一个目的地 ID。"""
    async with _direct_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id FROM destinations LIMIT 1")
        )
        row = result.fetchone()
        return row[0] if row else None


async def _get_first_base_service_id(_direct_engine) -> uuid.UUID | None:
    """获取 seed 数据中第一个基础服务 ID。"""
    async with _direct_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id FROM base_services LIMIT 1")
        )
        row = result.fetchone()
        return row[0] if row else None


class TestCustomTourAPI:
    """自定制旅程 API 功能测试（Session 16 新增功能测试）。"""

    async def test_submit_with_custom_destination(
        self, api_client: AsyncClient, _direct_engine
    ):
        """功能测试：提交含自定义目的地（custom_destination）的定制旅程。"""
        token = await _register_user(api_client)
        custom_dest = f"Custom Location {uuid.uuid4().hex[:6]}"

        resp = await api_client.post(
            "/api/v1/custom-tours/requests",
            json={
                "segments": [
                    {
                        "custom_destination": custom_dest,
                        "start_date": "2026-07-15",
                        "end_date": "2026-07-20",
                        "attraction_ids": [],
                        "tour_ids": [],
                    }
                ],
                "pax_count": 2,
                "guide_language": "en",
                "services": [],
                "contact_name": "Test User",
                "contact_email": f"ct_{uuid.uuid4().hex[:8]}@example.com",
                "contact_phone": "+1234567890",
                "locale": "en",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Submit failed: {resp.text}"
        data = resp.json()
        assert data["status"] == "ok"
        request_data = data["request"]

        # 验证响应包含 custom_destination
        assert len(request_data["segments"]) == 1
        segment = request_data["segments"][0]
        assert segment["custom_destination"] == custom_dest
        assert segment["destination_id"] is None  # 没有系统目的地
        assert segment["destination_name"] == custom_dest  # name 回退到 custom
        assert segment["start_date"] == "2026-07-15"
        assert segment["end_date"] == "2026-07-20"

        # 验证请求整体数据
        assert request_data["pax_count"] == 2
        assert request_data["contact_name"] == "Test User"
        assert request_data["status"] == "pending"

    async def test_submit_with_system_destination(
        self, api_client: AsyncClient, _direct_engine
    ):
        """功能测试：提交含系统目的地的定制旅程（向后兼容）。"""
        token = await _register_user(api_client)
        dest_id = await _get_first_destination_id(_direct_engine)
        if not dest_id:
            pytest.skip("No seed destination found")

        resp = await api_client.post(
            "/api/v1/custom-tours/requests",
            json={
                "segments": [
                    {
                        "destination_id": str(dest_id),
                        "start_date": "2026-08-01",
                        "end_date": "2026-08-05",
                        "attraction_ids": [],
                        "tour_ids": [],
                    }
                ],
                "pax_count": 3,
                "guide_language": "zh",
                "services": [],
                "contact_name": "System Dest User",
                "contact_email": f"ct_sys_{uuid.uuid4().hex[:8]}@example.com",
                "contact_phone": "+861380000000",
                "locale": "zh",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Submit failed: {resp.text}"
        data = resp.json()
        request_data = data["request"]

        assert len(request_data["segments"]) == 1
        segment = request_data["segments"][0]
        assert segment["destination_id"] == str(dest_id)
        assert segment["custom_destination"] is None
        assert segment["destination_name"] != ""  # 从翻译表获取

    async def test_submit_with_multi_segments_mixed_destinations(
        self, api_client: AsyncClient, _direct_engine
    ):
        """功能测试：多段行程混合系统目的地和自定义目的地。"""
        token = await _register_user(api_client)
        dest_id = await _get_first_destination_id(_direct_engine)
        if not dest_id:
            pytest.skip("No seed destination found")

        custom_dest = f"Custom Spot {uuid.uuid4().hex[:6]}"

        resp = await api_client.post(
            "/api/v1/custom-tours/requests",
            json={
                "segments": [
                    {
                        "destination_id": str(dest_id),
                        "start_date": "2026-09-01",
                        "end_date": "2026-09-03",
                        "attraction_ids": [],
                        "tour_ids": [],
                    },
                    {
                        "custom_destination": custom_dest,
                        "start_date": "2026-09-04",
                        "end_date": "2026-09-07",
                        "attraction_ids": [],
                        "tour_ids": [],
                    },
                ],
                "pax_count": 2,
                "guide_language": "en",
                "services": [],
                "contact_name": "Multi Segments",
                "contact_email": f"ct_multi_{uuid.uuid4().hex[:8]}@example.com",
                "locale": "en",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Submit failed: {resp.text}"
        data = resp.json()
        request_data = data["request"]

        assert len(request_data["segments"]) == 2

        seg1 = request_data["segments"][0]
        assert seg1["destination_id"] == str(dest_id)
        assert seg1["custom_destination"] is None
        assert seg1["destination_name"] != ""

        seg2 = request_data["segments"][1]
        assert seg2["destination_id"] is None
        assert seg2["custom_destination"] == custom_dest
        assert seg2["destination_name"] == custom_dest

    async def test_submit_without_destination_validates(
        self, api_client: AsyncClient, _direct_engine
    ):
        """鲁棒性测试：不提供 destination_id 和 custom_destination 仍然可提交（二者皆可选）。"""
        token = await _register_user(api_client)
        resp = await api_client.post(
            "/api/v1/custom-tours/requests",
            json={
                "segments": [
                    {
                        "start_date": "2026-10-01",
                        "end_date": "2026-10-03",
                        "attraction_ids": [],
                        "tour_ids": [],
                    }
                ],
                "pax_count": 1,
                "services": [],
                "contact_name": "No Dest",
                "contact_email": f"ct_nodest_{uuid.uuid4().hex[:8]}@example.com",
                "locale": "en",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Submit failed: {resp.text}"
        data = resp.json()
        segment = data["request"]["segments"][0]
        assert segment["destination_id"] is None
        assert segment["custom_destination"] is None
        assert segment["destination_name"] == ""

    async def test_submit_with_services(
        self, api_client: AsyncClient, _direct_engine
    ):
        """功能测试：提交含基础服务的定制旅程。"""
        token = await _register_user(api_client)
        svc_id = await _get_first_base_service_id(_direct_engine)

        services = []
        if svc_id:
            services = [{"service_id": str(svc_id), "quantity": 1}]

        resp = await api_client.post(
            "/api/v1/custom-tours/requests",
            json={
                "segments": [
                    {
                        "custom_destination": "Beach Resort with Service",
                        "start_date": "2026-11-01",
                        "end_date": "2026-11-05",
                        "attraction_ids": [],
                        "tour_ids": [],
                    }
                ],
                "pax_count": 2,
                "guide_language": "en",
                "services": services,
                "contact_name": "Svc User",
                "contact_email": f"ct_svc_{uuid.uuid4().hex[:8]}@example.com",
                "locale": "en",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Submit failed: {resp.text}"
        data = resp.json()
        request_data = data["request"]
        assert request_data["subtotal"] >= 0
        assert len(request_data["segments"]) == 1
        segment = request_data["segments"][0]
        assert segment["custom_destination"] == "Beach Resort with Service"

    async def test_quote_with_custom_destination(
        self, api_client: AsyncClient, _direct_engine
    ):
        """功能测试：自定义目的地报价计算不报错。"""
        token = await _register_user(api_client)

        resp = await api_client.post(
            "/api/v1/custom-tours/quote",
            json={
                "segments": [
                    {
                        "custom_destination": "Quote Custom Place",
                        "start_date": "2026-12-01",
                        "end_date": "2026-12-03",
                        "attraction_ids": [],
                        "tour_ids": [],
                    }
                ],
                "pax_count": 2,
                "services": [],
                "contact_name": "Quote User",
                "contact_email": f"ct_quote_{uuid.uuid4().hex[:8]}@example.com",
                "locale": "en",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Quote failed: {resp.text}"
        data = resp.json()
        assert data["subtotal"] == 0  # 无服务
        assert data["currency"] == "USD"
        assert "breakdown" in data
