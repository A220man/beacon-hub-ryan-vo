from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import BaseModel

from app.core.config import settings


class TokenPayload(BaseModel):
    sub: str
    preferred_username: str
    email: str | None = None
    realm_access: dict[str, list[str]] = {}
    resource_access: dict[str, dict[str, list[str]]] = {}
    exp: int
    iat: int
    iss: str
    aud: str | list[str]


@dataclass(frozen=True, slots=True)
class AuthUser:
    user_id: str
    username: str
    email: str | None
    roles: tuple[str, ...]

    @property
    def is_viewer(self) -> bool:
        return "viewer" in self.roles

    @property
    def is_operator(self) -> bool:
        return "operator" in self.roles

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles


class JWKSCache:
    def __init__(self, jwks_url: str, ttl_seconds: int = 3600):
        self.jwks_url = jwks_url
        self.ttl_seconds = ttl_seconds
        self._cached_keys: dict[str, Any] | None = None
        self._cached_at: float = 0

    async def get_keys(self) -> dict[str, Any]:
        now = time.time()
        if self._cached_keys is None or (now - self._cached_at) > self.ttl_seconds:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                self._cached_keys = response.json()
                self._cached_at = now
        return self._cached_keys


@lru_cache(maxsize=1)
def get_jwks_cache() -> JWKSCache:
    jwks_url = f"{settings.effective_oidc_issuer}/protocol/openid-connect/certs"
    return JWKSCache(jwks_url)


async def get_signing_key(token: str, jwks_cache: JWKSCache = Depends(get_jwks_cache)) -> dict[str, Any]:
    keys = await jwks_cache.get_keys()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing key ID",
        )
    for key in keys.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find matching signing key",
    )


async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> TokenPayload:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Get signing key
    jwks_cache = get_jwks_cache()
    keys = await jwks_cache.get_keys()
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing key ID",
        )
    signing_key = None
    for key in keys.get("keys", []):
        if key.get("kid") == kid:
            signing_key = key
            break
    if not signing_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find matching signing key",
        )

    try:
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[settings.algorithm],
            audience=settings.oidc_audience,
            issuer=settings.effective_oidc_issuer,
            options={"verify_aud": True, "verify_iss": True, "verify_exp": True},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    return TokenPayload(**payload)


def get_current_user(token_payload: TokenPayload = Depends(validate_token)) -> AuthUser:
    realm_roles = token_payload.realm_access.get("roles", [])
    client_roles = token_payload.resource_access.get(settings.keycloak_client_id, {}).get("roles", [])
    all_roles = tuple(set(realm_roles) | set(client_roles))
    return AuthUser(
        user_id=token_payload.sub,
        username=token_payload.preferred_username,
        email=token_payload.email,
        roles=all_roles,
    )


def require_viewer(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not user.is_viewer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: viewer role required",
        )
    return user


def require_operator(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not user.is_operator and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: operator role required",
        )
    return user


def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: admin role required",
        )
    return user


async def optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    signing_key: dict[str, Any] = Depends(get_signing_key),
) -> AuthUser | None:
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            signing_key,
            algorithms=[settings.algorithm],
            audience=settings.oidc_audience,
            issuer=settings.effective_oidc_issuer,
            options={"verify_aud": True, "verify_iss": True, "verify_exp": True},
        )
        token_payload = TokenPayload(**payload)
        return get_current_user(token_payload)
    except JWTError:
        return None