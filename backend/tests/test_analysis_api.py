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
async def test_analyze_recipe_endpoint(client: AsyncClient):
    recipe = {
        "name": "Test Recipe",
        "description": "Test",
        "target_build": "26100",
        "components": [
            {
                "name": "Microsoft.Edge",
                "category": "apps",
                "safe_to_remove": True,
                "size_mb": 180,
            },
            {
                "name": "DiagTrack",
                "category": "services",
                "safe_to_remove": True,
                "size_mb": 5,
            },
        ],
    }

    response = await client.post("/api/v1/analyze/recipe", json={"recipe": recipe, "target_build": "26100"})
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    analysis = data["analysis"]
    assert analysis["recipe_name"] == "Test Recipe"
    assert analysis["target_build"] == "26100"
    assert "overall_risk" in analysis
    assert "risk_score" in analysis
    assert "failure_predictions" in analysis
    assert len(analysis["failure_predictions"]) == 3
    assert "component_recommendations" in analysis


@pytest.mark.asyncio
async def test_analyze_recipe_endpoint_invalid(client: AsyncClient):
    response = await client.post("/api/v1/analyze/recipe", json={"recipe": "invalid", "target_build": "26100"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_advisor_components_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/analyze/advisor/components", json={
        "target_build": "26100",
        "categories": ["apps", "services"],
        "include_unsafe": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert isinstance(data["components"], list)
    assert len(data["components"]) > 0
    for comp in data["components"]:
        assert "component_name" in comp
        assert "category" in comp
        assert "recommended" in comp
        assert "risk_score" in comp


@pytest.mark.asyncio
async def test_advisor_components_endpoint_all_categories(client: AsyncClient):
    response = await client.post("/api/v1/analyze/advisor/components", json={
        "target_build": "26100",
        "include_unsafe": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["components"]) > 0


@pytest.mark.asyncio
async def test_advisor_database_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/analyze/advisor/database?target_build=26100")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert "target_build" in data
    assert "total_count" in data
    assert data["total_count"] > 0
    for comp in data["components"]:
        assert "name" in comp
        assert "category" in comp
        assert "safe_to_remove" in comp


@pytest.mark.asyncio
async def test_validate_autounattend_endpoint(client: AsyncClient):
    xml = """<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="windowsPE">
        <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
            <UserData>
                <ProductKey><Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key></ProductKey>
            </UserData>
        </component>
    </settings>
</unattend>
"""
    response = await client.post("/api/v1/validate/autounattend", json={"xml": xml})
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    assert "issues" in data
    assert "passes_found" in data
    assert "components_referenced" in data


@pytest.mark.asyncio
async def test_validate_autounattend_endpoint_missing_product_key(client: AsyncClient):
    xml = """<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="windowsPE">
        <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
            <UserData>
                <ProductKey><Key></Key></ProductKey>
            </UserData>
        </component>
    </settings>
</unattend>
"""
    response = await client.post("/api/v1/validate/autounattend", json={"xml": xml})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any(i["code"] == "MISSING_PRODUCT_KEY" for i in data["issues"])


@pytest.mark.asyncio
async def test_validate_autounattend_endpoint_empty(client: AsyncClient):
    response = await client.post("/api/v1/validate/autounattend", json={"xml": ""})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_validate_autounattend_endpoint_malformed(client: AsyncClient):
    response = await client.post("/api/v1/validate/autounattend", json={"xml": "<invalid>"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any(i["code"] == "XML_PARSE_ERROR" for i in data["issues"])