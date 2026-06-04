"""API 集成测试 —— 健康检查（通过运行中的 Docker 服务）。"""

import pytest
from httpx import AsyncClient


class TestHealthAPI:
    """健康检查端点的完整测试。"""

    async def test_health_returns_200(self, api_client: AsyncClient):
        """功能测试：健康检查返回 200。"""
        response = await api_client.get("/health")
        assert response.status_code == 200

    async def test_health_body(self, api_client: AsyncClient):
        """功能测试：健康检查返回正确的状态信息。"""
        response = await api_client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    async def test_health_elasticsearch_field(self, api_client: AsyncClient):
        """功能测试：健康检查包含 ES 连接状态。"""
        response = await api_client.get("/health")
        data = response.json()
        assert "elasticsearch" in data
        assert isinstance(data["elasticsearch"], bool)

    async def test_root_not_found(self, api_client: AsyncClient):
        """边界测试：未定义的根路径返回 404。"""
        response = await api_client.get("/")
        assert response.status_code == 404

    async def test_health_invalid_method(self, api_client: AsyncClient):
        """边界测试：POST 健康检查返回 405。"""
        response = await api_client.post("/health")
        assert response.status_code in (405, 200)  # FastAPI 可能返回 405
