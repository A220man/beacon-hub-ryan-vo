from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient
from jose import jwt

from app.core.auth import TokenPayload
from app.main import create_app


VALID_PAYLOAD = {
    "sub": "kc-user-123",
    "preferred_username": "realuser",
    "email": "real@example.com",
    "realm_access": {"roles": ["viewer", "operator"]},
    "resource_access": {},
    "exp": 9999999999,
    "iat": 0,
    "iss": "http://test/realms/test",
    "aud": "account",
}


def _make_client() -> TestClient:
    return TestClient(create_app())


def _token_response(token: str = "header.kid.sig") -> httpx.Response:
    return httpx.Response(200, json={"id_token": token, "access_token": "at"})


def test_callback_exchanges_code_and_returns_real_user():
    """Callback exchanges the PKCE code with Keycloak and returns validated user."""
    client = _make_client()
    with patch(
        "app.api.auth._exchange_code_for_tokens",
        new=AsyncMock(return_value={"id_token": "signed-token", "access_token": "at"}),
    ), patch(
        "app.api.auth._validate_id_token",
        new=AsyncMock(return_value=TokenPayload(**VALID_PAYLOAD)),
    ):
        response = client.post(
            "/api/v1/auth/callback",
            json={"code": "auth-code", "verifier": "verifier-value"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["id_token"] == "signed-token"
    assert body["user"]["user_id"] == "kc-user-123"
    assert body["user"]["username"] == "realuser"
    assert body["user"]["email"] == "real@example.com"
    assert set(body["user"]["roles"]) == {"viewer", "operator"}


def test_callback_rejects_missing_verifier():
    """Missing PKCE verifier is rejected before any token exchange."""
    client = _make_client()
    response = client.post(
        "/api/v1/auth/callback",
        json={"code": "auth-code", "verifier": ""},
    )
    assert response.status_code == 400


def test_callback_surfaces_keycloak_exchange_error():
    """A non-200 token-endpoint response yields 401 with the Keycloak detail."""
    client = _make_client()
    err_response = httpx.Response(400, json={"error": "invalid_grant", "error_description": "Code not valid"})

    async def fake_post(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        return err_response

    with patch("httpx.AsyncClient.post", new=fake_post):
        response = client.post(
            "/api/v1/auth/callback",
            json={"code": "bad-code", "verifier": "verifier-value"},
        )

    assert response.status_code == 401
    assert "Code not valid" in response.json()["detail"]
