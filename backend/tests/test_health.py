from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client: AsyncClient):
    response = await client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_endpoint_version_matches_settings(client: AsyncClient):
    response = await client.get("/api/v1/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert data["environment"] == "development"