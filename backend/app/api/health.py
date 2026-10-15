from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import Settings, settings


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check(cfg: Settings = Depends(lambda: settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=cfg.app_version,
        environment=cfg.environment,
    )