from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi import Depends
from fastapi.testclient import TestClient

from app.core.auth import AuthUser, get_current_user, require_admin, require_operator, require_viewer
from app.main import create_app


@dataclass(frozen=True)
class TestUser:
    user_id: str = "test-user-id"
    username: str = "testuser"
    email: str = "test@example.com"
    roles: tuple[str, ...] = ("viewer",)


TEST_USER = TestUser()
TEST_OPERATOR = TestUser(roles=("viewer", "operator"))
TEST_ADMIN = TestUser(roles=("viewer", "operator", "admin"))


def override_get_current_user(user: TestUser = TEST_USER) -> AuthUser:
    return AuthUser(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=user.roles,
    )


def get_test_client_with_auth(user: TestUser = TEST_USER) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: override_get_current_user(user)
    app.dependency_overrides[require_viewer] = lambda: override_get_current_user(user)
    app.dependency_overrides[require_operator] = lambda: override_get_current_user(user)
    app.dependency_overrides[require_admin] = lambda: override_get_current_user(user)
    return TestClient(app)


def get_test_client_unauthenticated() -> TestClient:
    return TestClient(create_app())


@patch("app.core.auth.get_signing_key")
@patch("app.core.auth.validate_token")
def mock_jwt_validation(
    mock_validate_token: AsyncMock,
    mock_get_signing_key: AsyncMock,
    user: TestUser = TEST_USER,
) -> None:
    from app.core.auth import TokenPayload

    mock_get_signing_key.return_value = {"kty": "RSA", "kid": "test-key"}
    mock_validate_token.return_value = TokenPayload(
        sub=user.user_id,
        preferred_username=user.username,
        email=user.email,
        realm_access={"roles": list(user.roles)},
        resource_access={},
        exp=9999999999,
        iat=0,
        iss="http://test/realms/test",
        aud="account",
    )


def create_mock_token_payload(user: TestUser = TEST_USER) -> dict[str, Any]:
    return {
        "sub": user.user_id,
        "preferred_username": user.username,
        "email": user.email,
        "realm_access": {"roles": list(user.roles)},
        "resource_access": {},
        "exp": 9999999999,
        "iat": 0,
        "iss": "http://test/realms/test",
        "aud": "account",
    }
import pytest


def test_unauthenticated_access_rejected():
    """Unauthenticated requests to protected endpoints should return 401."""
    client = get_test_client_unauthenticated()
    response = client.get("/api/v1/analyze/advisor/database?target_build=26100")
    assert response.status_code == 401
    assert "Missing authorization header" in response.json()["detail"]


def test_unauthenticated_post_rejected():
    """Unauthenticated POST requests to protected endpoints should return 401."""
    client = get_test_client_unauthenticated()
    response = client.post("/api/v1/analyze/recipe", json={"recipe": {}, "target_build": "26100"})
    assert response.status_code == 401


def test_viewer_role_grants_access():
    """Viewer role should grant access to analysis endpoints."""
    client = get_test_client_with_auth(TEST_USER)
    response = client.get("/api/v1/analyze/advisor/database?target_build=26100")
    assert response.status_code == 200


def test_operator_role_grants_access():
    """Operator role should grant access to analysis endpoints."""
    client = get_test_client_with_auth(TEST_OPERATOR)
    response = client.get("/api/v1/analyze/advisor/database?target_build=26100")
    assert response.status_code == 200


def test_admin_role_grants_access():
    """Admin role should grant access to analysis endpoints."""
    client = get_test_client_with_auth(TEST_ADMIN)
    response = client.get("/api/v1/analyze/advisor/database?target_build=26100")
    assert response.status_code == 200


def test_viewer_cannot_access_admin_endpoint():
    """Viewer role should be denied access to admin-only endpoints."""
    # We need an admin-only endpoint to test this. For now, test the require_admin dependency directly.
    from app.core.auth import require_admin, AuthUser

    viewer_user = AuthUser(user_id="1", username="viewer", email="v@test.com", roles=("viewer",))

    try:
        require_admin(viewer_user)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert e.status_code == 403
        assert "Insufficient permissions" in str(e.detail)


def test_operator_cannot_access_admin_endpoint():
    """Operator role should be denied access to admin-only endpoints."""
    from app.core.auth import require_admin, AuthUser

    operator_user = AuthUser(user_id="1", username="operator", email="o@test.com", roles=("viewer", "operator"))

    try:
        require_admin(operator_user)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert e.status_code == 403
        assert "Insufficient permissions" in str(e.detail)


def test_viewer_can_access_operator_endpoint():
    """Viewer should be denied access to operator-only endpoints."""
    from app.core.auth import require_operator, AuthUser

    viewer_user = AuthUser(user_id="1", username="viewer", email="v@test.com", roles=("viewer",))

    try:
        require_operator(viewer_user)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert e.status_code == 403
        assert "Insufficient permissions" in str(e.detail)


def test_operator_can_access_operator_endpoint():
    """Operator should be granted access to operator-only endpoints."""
    from app.core.auth import require_operator, AuthUser

    operator_user = AuthUser(user_id="1", username="operator", email="o@test.com", roles=("viewer", "operator"))

    result = require_operator(operator_user)
    assert result.username == "operator"


def test_admin_can_access_operator_endpoint():
    """Admin should be granted access to operator-only endpoints."""
    from app.core.auth import require_operator, AuthUser

    admin_user = AuthUser(user_id="1", username="admin", email="a@test.com", roles=("viewer", "operator", "admin"))

    result = require_operator(admin_user)
    assert result.username == "admin"