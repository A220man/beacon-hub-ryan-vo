from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel

from app.services.answer_validator import validate_autounattend, ValidationSeverity
from app.models.answer_file import ValidationIssue

router = APIRouter(prefix="/api/v1/validate", tags=["validation"])


class ValidateAutounattendRequest(BaseModel):
    xml: str


class ValidateAutounattendResponse(BaseModel):
    valid: bool
    issues: list[dict]
    passes_found: list[str]
    components_referenced: list[str]


def _severity_to_int(sev: ValidationSeverity) -> int:
    order = {
        ValidationSeverity.ERROR: 0,
        ValidationSeverity.WARNING: 1,
        ValidationSeverity.INFO: 2,
    }
    return order.get(sev, 3)


@router.post("/autounattend", response_model=ValidateAutounattendResponse)
async def validate_autounattend_endpoint(request: ValidateAutounattendRequest) -> ValidateAutounattendResponse:
    if not request.xml or not request.xml.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="XML content is required",
        )

    if len(request.xml) > 1_000_000:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="XML content too large (max 1MB)",
        )

    try:
        result = validate_autounattend(request.xml)
        sorted_issues = sorted(result.issues, key=lambda i: _severity_to_int(i.severity))
        return ValidateAutounattendResponse(
            valid=result.valid,
            issues=[i.to_dict() for i in sorted_issues],
            passes_found=[p.value for p in result.passes_found],
            components_referenced=list(result.components_referenced),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {e}",
        ) from e