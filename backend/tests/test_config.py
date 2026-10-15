from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.app_name == "beacon-hub"
    assert s.app_version == "1.0.0"
    assert s.environment == "development"
    assert s.debug is True
    assert s.host == "0.0.0.0"
    assert s.port == 8000
    assert s.database_url == "sqlite+aiosqlite:///./beacon.db"
    assert s.algorithm == "HS256"
    assert s.access_token_expire_minutes == 30


def test_settings_secret_key_min_length():
    with pytest.raises(ValidationError):
        Settings(secret_key="short")


def test_settings_cors_origins_default():
    s = Settings()
    assert "http://localhost:5173" in s.cors_origins


def test_settings_is_production_property():
    s = Settings(environment="production")
    assert s.is_production is True

    s = Settings(environment="development")
    assert s.is_production is False


def test_settings_effective_oidc_issuer():
    s = Settings(keycloak_url="https://auth.example.com", keycloak_realm="test")
    assert s.effective_oidc_issuer == "https://auth.example.com/realms/test"

    s = Settings(oidc_issuer="https://custom.issuer")
    assert s.effective_oidc_issuer == "https://custom.issuer"


def test_settings_llm_defaults():
    s = Settings()
    assert s.llm_provider == "openai-compatible"
    assert s.llm_model == "gpt-4o-mini"
    assert s.llm_base_url == "https://api.openai.com/v1"