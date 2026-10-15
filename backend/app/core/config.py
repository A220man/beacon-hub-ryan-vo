from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    secret_key: str = Field(default="dev-secret-change-in-production-must-be-32-chars-minimum", min_length=32)
    # Application
    app_name: str = "beacon-hub"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./beacon.db"

    # Security
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Keycloak / OIDC
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "beacon-hub"
    keycloak_client_id: str = "beacon-frontend"
    keycloak_client_secret: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = "account"

    # LLM (optional)
    llm_api_key: str = ""
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def effective_oidc_issuer(self) -> str:
        if self.oidc_issuer:
            return self.oidc_issuer
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"


settings = Settings()