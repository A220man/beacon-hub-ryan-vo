from __future__ import annotations

from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.auth import TokenPayload, get_current_user, validate_token
from app.core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TokenExchangeRequest(BaseModel):
    code: str
    verifier: str
    state: Optional[dict] = None


class AuthCallbackResponse(BaseModel):
    user: dict
    id_token: str


def _token_endpoint() -> str:
    return f"{settings.effective_oidc_issuer}/protocol/openid-connect/token"


async def _exchange_code_for_tokens(code: str, verifier: str) -> dict[str, Any]:
    """Exchange a Keycloak authorization code for tokens using PKCE.

    Calls the Keycloak token endpoint with the standard
    ``grant_type=authorization_code`` flow and returns the parsed token
    response. Raises HTTPException on any transport or token-endpoint
    failure.
    """
    form = {
        "grant_type": "authorization_code",
        "client_id": settings.keycloak_client_id,
        "code": code,
        "code_verifier": verifier,
    }
    if settings.keycloak_client_secret:
        form["client_secret"] = settings.keycloak_client_secret

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(_token_endpoint(), data=form)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach Keycloak token endpoint: {exc}",
        ) from exc

    if response.status_code != 200:
        # Surface the Keycloak error description when present.
        detail = response.text
        try:
            err = response.json()
            detail = err.get("error_description") or err.get("error") or detail
        except ValueError:
            pass
        raise HTTPException(
            status_code=401,
            detail=f"Token exchange failed: {detail}",
        )

    return response.json()


async def _validate_id_token(id_token: str) -> TokenPayload:
    """Validate a Keycloak-issued id_token using the shared bearer validator."""
    from fastapi.security import HTTPAuthorizationCredentials

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=id_token)
    return await validate_token(credentials)


@router.post("/callback", response_model=AuthCallbackResponse)
async def auth_callback(payload: TokenExchangeRequest, request: Request):
    """Exchange a Keycloak authorization code for tokens using PKCE.

    The backend exchanges the code with Keycloak's token endpoint,
    validates the resulting id_token (signature, audience, issuer, expiry),
    and returns the real user profile plus the id_token so the frontend can
    store it for subsequent bearer-authenticated API calls.
    """
    if not payload.code or not payload.verifier:
        raise HTTPException(status_code=400, detail="Missing code or PKCE verifier")

    tokens = await _exchange_code_for_tokens(payload.code, payload.verifier)
    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(status_code=401, detail="Keycloak did not return an id_token")

    token_payload = await _validate_id_token(id_token)
    user = get_current_user(token_payload)

    return AuthCallbackResponse(
        user={
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": list(user.roles),
        },
        id_token=id_token,
    )
