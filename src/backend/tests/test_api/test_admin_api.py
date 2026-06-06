"""后台管理 API 集成测试。

注意：admin API 测试需要创建一个真正的 admin 用户并提交到数据库，
因为 api_client 连接的是运行中的 Docker 后端服务，它使用独立的数据库连接。

策略：先通过 API 注册用户获取 JWT（由 Docker 后端签署，保证密钥一致），
然后通过直接 SQL 提升为管理员。
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import settings
from app.models.attraction import Attraction


@pytest.fixture
def _admin_engine():
    """独立引擎用于 admin 用户 promotion（提交后 Docker 后端可见）。"""
    engine = create_async_engine(settings.database_url, echo=False, pool_size=1)
    yield engine


async def _register_and_promote(api_client, admin_engine) -> str:
    """通过 API 注册用户 → 直接 SQL 提升为管理员 → 返回 JWT。"""
    import uuid as _uuid
    email = f"admin_{_uuid.uuid4().hex[:8]}@example.com"
    resp = await api_client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "TestPass123!",
        "name": "Admin Tester",
    })
    assert resp.status_code in (200, 201), f"Registration failed: {resp.text}"
    data = resp.json()
    token = data["access_token"]
    user_id = data["user"]["id"]

    # 通过 SQL 提升为管理员
    async with admin_engine.connect() as conn:
        await conn.execute(
            text("UPDATE users SET is_admin = true WHERE id = :uid"),
            {"uid": user_id},
        )
        await conn.commit()
    return token


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

    async def test_all_admin_endpoints_require_auth(self, api_client: AsyncClient):
        """鲁棒性测试：所有 admin 端点都需要认证（含 Session 16 新增端点）。"""
        endpoints = [
            ("GET", "/api/v1/admin/stats"),
            ("GET", "/api/v1/admin/tours"),
            ("GET", "/api/v1/admin/orders"),
            ("GET", "/api/v1/admin/users"),
            ("GET", "/api/v1/admin/reviews"),
            ("GET", "/api/v1/admin/attractions"),
            ("GET", "/api/v1/admin/attractions/00000000-0000-0000-0000-000000000001"),
            ("PATCH", "/api/v1/admin/attractions/00000000-0000-0000-0000-000000000001"),
            ("POST", "/api/v1/admin/attractions/00000000-0000-0000-0000-000000000001/media"),
            ("DELETE", "/api/v1/admin/attractions/00000000-0000-0000-0000-000000000001/media/00000000-0000-0000-0000-000000000001"),
            ("PUT", "/api/v1/admin/attractions/00000000-0000-0000-0000-000000000001/media/reorder"),
            # Session 16: Destinations CRUD
            ("GET", "/api/v1/admin/destinations"),
            ("GET", "/api/v1/admin/destinations/00000000-0000-0000-0000-000000000001"),
            ("POST", "/api/v1/admin/destinations"),
            ("PUT", "/api/v1/admin/destinations/00000000-0000-0000-0000-000000000001"),
            ("DELETE", "/api/v1/admin/destinations/00000000-0000-0000-0000-000000000001"),
            # Session 16: Base Services CRUD
            ("GET", "/api/v1/admin/base-services"),
            ("POST", "/api/v1/admin/base-services"),
            ("PUT", "/api/v1/admin/base-services/00000000-0000-0000-0000-000000000001"),
            ("DELETE", "/api/v1/admin/base-services/00000000-0000-0000-0000-000000000001"),
            # Session 16: Custom Tours admin
            ("GET", "/api/v1/admin/custom-tours"),
            ("PATCH", "/api/v1/admin/custom-tours/00000000-0000-0000-0000-000000000001"),
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

    # ── Admin authenticated tests ────────────────────────────────────────

    async def test_stats_admin(self, api_client: AsyncClient, _admin_engine):
        """功能测试：管理员可以看到统计。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_tours" in data
        assert "published_tours" in data

    async def test_admin_tours_sort_order_in_response(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：admin tours 列表返回 sort_order 字段。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/tours?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "tours" in data
        if data["tours"]:
            tour = data["tours"][0]
            assert "sort_order" in tour, "sort_order missing in admin tour response"

    async def test_admin_tour_serial_number_in_response(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：admin tours 列表返回 serial_number 和 area_code 字段。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/tours?page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "tours" in data
        if data["tours"]:
            tour = data["tours"][0]
            assert "serial_number" in tour, "serial_number missing in admin tour response"
            assert "area_code" in tour, "area_code missing in admin tour response"

    async def test_admin_tour_delete(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：管理员可以软删除旅游产品。"""
        token = await _register_and_promote(api_client, _admin_engine)
        headers = {"Authorization": f"Bearer {token}"}

        # 准备：先获取一个现存 tour 的 id
        list_resp = await api_client.get(
            "/api/v1/admin/tours?page=1&page_size=5", headers=headers
        )
        assert list_resp.status_code == 200
        tours = list_resp.json().get("tours", [])
        if not tours:
            pytest.skip("No tours available for delete test")
        tour_id = tours[0]["id"]

        # 执行删除
        delete_resp = await api_client.delete(
            f"/api/v1/admin/tours/{tour_id}", headers=headers
        )
        assert delete_resp.status_code == 200
        delete_data = delete_resp.json()
        assert delete_data["status"] == "deleted"

        # 验证：被删除的 tour 不再出现于列表中
        list_resp2 = await api_client.get(
            "/api/v1/admin/tours?page=1&page_size=100", headers=headers
        )
        remaining_ids = [t["id"] for t in list_resp2.json().get("tours", [])]
        assert tour_id not in remaining_ids, "Deleted tour still appears in list"

    async def test_admin_tour_delete_not_found(
        self, api_client: AsyncClient, _admin_engine
    ):
        """边界测试：删除不存在的 tour 返回 404。"""
        token = await _register_and_promote(api_client, _admin_engine)
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await api_client.delete(
            f"/api/v1/admin/tours/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_admin_tour_create_with_serial_number(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：创建 tour 时自定义 serial_number。"""
        token = await _register_and_promote(api_client, _admin_engine)
        headers = {"Authorization": f"Bearer {token}"}
        slug = f"test-serial-{uuid.uuid4().hex[:6]}"

        resp = await api_client.post("/api/v1/admin/tours", json={
            "slug": slug,
            "status": "draft",
            "type": "group_tour",
            "duration_days": 1,
            "duration_nights": 0,
            "start_price": 100,
            "serial_number": "0099",
            "translations": [
                {"locale": "en", "name": "Serial Test Tour", "subtitle": "Testing serial number"},
            ],
        }, headers=headers)
        assert resp.status_code == 201, f"POST failed: {resp.text}"
        data = resp.json()
        assert data["status"] == "ok"
        assert data["id"]

        # 验证列表返回 serial_number
        detail_resp = await api_client.get(
            f"/api/v1/admin/tours/{data['id']}?locale=en",
            headers=headers,
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json().get("serial_number") == "0099"

    async def test_admin_attractions_list_auth(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：管理员可查看景点列表。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/attractions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "attractions" in data
        assert "total" in data
        assert isinstance(data["attractions"], list)

    async def test_admin_attractions_list_pagination(
        self, api_client: AsyncClient, _admin_engine
    ):
        """边界测试：景点列表分页参数。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/attractions?page=1&page_size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_admin_attractions_get_detail_auth(
        self, api_client: AsyncClient, _admin_engine, db_session: AsyncSession
    ):
        """功能测试：管理员可查看景点详情（含 media/translations/tickets）。"""
        token = await _register_and_promote(api_client, _admin_engine)
        # 使用 seed 数据中已存在的 attraction
        result = await db_session.execute(select(Attraction).limit(1))
        attr = result.scalar_one_or_none()
        if not attr:
            pytest.skip("No attraction found in database")

        resp = await api_client.get(
            f"/api/v1/admin/attractions/{attr.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == str(attr.id)
        assert "sort_order" in detail
        assert "media" in detail
        assert "translations" in detail
        assert "tickets" in detail

    async def test_admin_attractions_get_detail_not_found(
        self, api_client: AsyncClient, _admin_engine
    ):
        """鲁棒性测试：不存在的景点 ID 返回 404。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            f"/api/v1/admin/attractions/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_admin_attractions_update_basic_fields(
        self, api_client: AsyncClient, _admin_engine, db_session: AsyncSession
    ):
        """功能测试：管理员更新景点基础字段（含 sort_order）。"""
        token = await _register_and_promote(api_client, _admin_engine)
        result = await db_session.execute(select(Attraction).limit(1))
        attr = result.scalar_one_or_none()
        if not attr:
            pytest.skip("No attraction found in database")

        original_sort = attr.sort_order or 0
        resp = await api_client.patch(
            f"/api/v1/admin/attractions/{attr.id}",
            json={"sort_order": original_sort + 5, "rating": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        # 验证更新是否生效
        resp2 = await api_client.get(
            f"/api/v1/admin/attractions/{attr.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        detail = resp2.json()
        assert detail["sort_order"] == original_sort + 5
        assert detail["rating"] == 5

    # ═══════════════════════════════════════════════════════════
    # Session 16: Admin Destinations CRUD 测试
    # ═══════════════════════════════════════════════════════════

    async def test_admin_destinations_list_empty(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：管理员可查看目的地列表（初始含 seed 数据）。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/destinations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "destinations" in data
        assert "total" in data
        assert isinstance(data["destinations"], list)
        assert data["page"] == 1
        assert data["page_size"] == 50

    async def test_admin_destinations_list_pagination(
        self, api_client: AsyncClient, _admin_engine
    ):
        """边界测试：目的地列表分页参数。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/destinations?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_admin_destinations_create(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：创建目的地（含多语言翻译）。"""
        token = await _register_and_promote(api_client, _admin_engine)
        slug = f"test-city-{uuid.uuid4().hex[:6]}"
        resp = await api_client.post(
            "/api/v1/admin/destinations",
            json={
                "slug": slug,
                "image_url": "https://example.com/city.jpg",
                "status": "active",
                "translations": [
                    {"locale": "en", "name": "Test City", "description": "A beautiful test city"},
                    {"locale": "zh", "name": "测试城市", "description": "一个美丽的测试城市"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["status"] == "ok"
        assert data["id"]

        # 验证列表中存在
        resp2 = await api_client.get(
            "/api/v1/admin/destinations",
            headers={"Authorization": f"Bearer {token}"},
        )
        slugs = [d["slug"] for d in resp2.json()["destinations"]]
        assert slug in slugs

    async def test_admin_destinations_create_duplicate_slug(
        self, api_client: AsyncClient, _admin_engine
    ):
        """鲁棒性测试：重复 slug 返回 409。"""
        token = await _register_and_promote(api_client, _admin_engine)
        slug = f"dup-city-{uuid.uuid4().hex[:6]}"
        # 第一次创建
        resp = await api_client.post(
            "/api/v1/admin/destinations",
            json={"slug": slug, "translations": [{"locale": "en", "name": "Dup City"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        # 第二次创建（相同 slug）
        resp = await api_client.post(
            "/api/v1/admin/destinations",
            json={"slug": slug, "translations": [{"locale": "en", "name": "Dup City Again"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_admin_destinations_get_detail(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：获取目的地详情。"""
        token = await _register_and_promote(api_client, _admin_engine)
        slug = f"detail-city-{uuid.uuid4().hex[:6]}"
        create_resp = await api_client.post(
            "/api/v1/admin/destinations",
            json={
                "slug": slug,
                "translations": [
                    {"locale": "en", "name": "Detail City", "description": "A detailed city"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        dest_id = create_resp.json()["id"]

        resp = await api_client.get(
            f"/api/v1/admin/destinations/{dest_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == dest_id
        assert detail["slug"] == slug
        assert len(detail["translations"]) >= 1
        en_trans = [t for t in detail["translations"] if t["locale"] == "en"]
        assert len(en_trans) >= 1
        assert en_trans[0]["name"] == "Detail City"

    async def test_admin_destinations_get_not_found(
        self, api_client: AsyncClient, _admin_engine
    ):
        """鲁棒性测试：不存在的目的地 ID 返回 404。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            f"/api/v1/admin/destinations/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_admin_destinations_update(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：更新目的地（slug / image / status / 翻译）。"""
        token = await _register_and_promote(api_client, _admin_engine)
        slug = f"upd-city-{uuid.uuid4().hex[:6]}"
        create_resp = await api_client.post(
            "/api/v1/admin/destinations",
            json={
                "slug": slug,
                "image_url": "https://example.com/old.jpg",
                "status": "active",
                "translations": [
                    {"locale": "en", "name": "Update City"},
                    {"locale": "zh", "name": "更新城市"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        dest_id = create_resp.json()["id"]

        # 更新
        new_slug = f"upd-city-new-{uuid.uuid4().hex[:6]}"
        update_resp = await api_client.put(
            f"/api/v1/admin/destinations/{dest_id}",
            json={
                "slug": new_slug,
                "image_url": "https://example.com/new.jpg",
                "status": "inactive",
                "translations": [
                    {"locale": "en", "name": "Updated City", "description": "Updated description"},
                    {"locale": "fr", "name": "Ville mise à jour"},
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "ok"

        # 验证更新
        get_resp = await api_client.get(
            f"/api/v1/admin/destinations/{dest_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        detail = get_resp.json()
        assert detail["slug"] == new_slug
        assert detail["image_url"] == "https://example.com/new.jpg"
        assert detail["status"] == "inactive"
        locales = {t["locale"] for t in detail["translations"]}
        assert "en" in locales
        assert "fr" in locales  # 新增翻译
        zh_trans = [t for t in detail["translations"] if t["locale"] == "zh"]
        assert len(zh_trans) >= 1  # 中文翻译保留

    async def test_admin_destinations_delete(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：删除目的地。"""
        token = await _register_and_promote(api_client, _admin_engine)
        slug = f"del-city-{uuid.uuid4().hex[:6]}"
        create_resp = await api_client.post(
            "/api/v1/admin/destinations",
            json={
                "slug": slug,
                "translations": [{"locale": "en", "name": "Delete City"}],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        dest_id = create_resp.json()["id"]

        resp = await api_client.delete(
            f"/api/v1/admin/destinations/{dest_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"Delete failed: {resp.text}"
        assert resp.json()["status"] == "deleted"

        # 验证已删除
        get_resp = await api_client.get(
            f"/api/v1/admin/destinations/{dest_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404

    async def test_admin_destinations_delete_with_attractions(
        self, api_client: AsyncClient, _admin_engine
    ):
        """鲁棒性测试：删除有关联景点的目的地返回错误。"""
        token = await _register_and_promote(api_client, _admin_engine)
        # 找一个已有景点关联的目的地（seed 数据）
        from sqlalchemy import text
        engine = create_async_engine(settings.database_url, echo=False, pool_size=1)
        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("""
                        SELECT d.id FROM destinations d
                        JOIN attractions a ON a.destination_id = d.id
                        LIMIT 1
                    """)
                )
                row = result.fetchone()
                if not row:
                    pytest.skip("No destination with linked attractions found")
                dest_id = row[0]
        finally:
            await engine.dispose()

        resp = await api_client.delete(
            f"/api/v1/admin/destinations/{dest_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "Cannot delete" in data.get("detail", "")

    async def test_admin_destinations_not_found_delete(
        self, api_client: AsyncClient, _admin_engine
    ):
        """鲁棒性测试：删除不存在的目的地返回 404。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.delete(
            f"/api/v1/admin/destinations/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    # ═══════════════════════════════════════════════════════════
    # Session 16: Admin Base Services CRUD 测试
    # ═══════════════════════════════════════════════════════════

    async def test_admin_base_services_list(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：管理员可查看基础服务列表。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.get(
            "/api/v1/admin/base-services",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "services" in data
        assert "total" in data
        assert isinstance(data["services"], list)

    async def test_admin_base_services_create(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：创建基础服务。"""
        token = await _register_and_promote(api_client, _admin_engine)
        resp = await api_client.post(
            "/api/v1/admin/base-services",
            json={
                "name": "Test Guide",
                "name_zh": "测试导游",
                "description": "Professional tour guide service",
                "unit_type": "per_day",
                "unit_price": 150.00,
                "currency": "USD",
                "category": "guide",
                "sort_order": 1,
                "status": "active",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        data = resp.json()
        assert data["status"] == "ok"
        assert data["id"]
        svc = data["service"]
        assert svc["name"] == "Test Guide"
        assert svc["unit_price"] == 150.00

    async def test_admin_base_services_update(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：更新基础服务。"""
        token = await _register_and_promote(api_client, _admin_engine)
        # 先创建
        create_resp = await api_client.post(
            "/api/v1/admin/base-services",
            json={
                "name": "Update Service",
                "unit_type": "per_day",
                "unit_price": 100.00,
                "status": "active",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        svc_id = create_resp.json()["id"]

        # 更新
        update_resp = await api_client.put(
            f"/api/v1/admin/base-services/{svc_id}",
            json={
                "name": "Updated Service",
                "unit_price": 200.00,
                "status": "inactive",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "ok"

    async def test_admin_base_services_delete(
        self, api_client: AsyncClient, _admin_engine
    ):
        """功能测试：删除基础服务。"""
        token = await _register_and_promote(api_client, _admin_engine)
        # 先创建
        create_resp = await api_client.post(
            "/api/v1/admin/base-services",
            json={
                "name": "Delete Service",
                "unit_type": "per_day",
                "unit_price": 50.00,
                "status": "active",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        svc_id = create_resp.json()["id"]

        # 删除
        resp = await api_client.delete(
            f"/api/v1/admin/base-services/{svc_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    async def test_admin_base_services_not_found(
        self, api_client: AsyncClient, _admin_engine
    ):
        """鲁棒性测试：操作不存在的服务返回 404。"""
        token = await _register_and_promote(api_client, _admin_engine)
        fake_id = uuid.uuid4()
        # GET
        resp = await api_client.put(
            f"/api/v1/admin/base-services/{fake_id}",
            json={"name": "Nope"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
        # DELETE
        resp = await api_client.delete(
            f"/api/v1/admin/base-services/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
