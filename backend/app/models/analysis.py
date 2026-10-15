from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailureType(str, Enum):
    DISM_PENDING_OPERATIONS = "dism_pending_operations"
    REGISTRY_ACCESS_DENIED = "registry_access_denied"
    ADK_VERSION_MISMATCH = "adk_version_mismatch"
    ANSWER_FILE_PRODUCT_KEY = "answer_file_product_key"
    ANSWER_FILE_LOCALE = "answer_file_locale"
    COMPONENT_DEPENDENCY = "component_dependency"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FailurePrediction:
    failure_type: FailureType
    probability: float
    risk_level: RiskLevel
    description: str
    evidence: list[str] = field(default_factory=list)
    mitigation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_type": self.failure_type.value,
            "probability": self.probability,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "evidence": self.evidence,
            "mitigation": self.mitigation,
        }


@dataclass(frozen=True, slots=True)
class ComponentRecommendation:
    component_name: str
    category: str
    recommended: bool
    reason: str
    risk_score: float
    dependencies_satisfied: bool = True
    conflicts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_name": self.component_name,
            "category": self.category,
            "recommended": self.recommended,
            "reason": self.reason,
            "risk_score": self.risk_score,
            "dependencies_satisfied": self.dependencies_satisfied,
            "conflicts": list(self.conflicts),
        }


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    recipe_name: str
    target_build: str
    analyzed_at: datetime
    overall_risk: RiskLevel
    risk_score: float
    failure_predictions: tuple[FailurePrediction, ...]
    component_recommendations: tuple[ComponentRecommendation, ...]
    warnings: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_name": self.recipe_name,
            "target_build": self.target_build,
            "analyzed_at": self.analyzed_at.isoformat(),
            "overall_risk": self.overall_risk.value,
            "risk_score": self.risk_score,
            "failure_predictions": [p.to_dict() for p in self.failure_predictions],
            "component_recommendations": [r.to_dict() for r in self.component_recommendations],
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }

    @classmethod
    def create_low_risk(
        cls,
        recipe_name: str,
        target_build: str,
        metadata: dict[str, Any] | None = None,
    ) -> AnalysisResult:
        return cls(
            recipe_name=recipe_name,
            target_build=target_build,
            analyzed_at=datetime.now(timezone.utc),
            overall_risk=RiskLevel.LOW,
            risk_score=0.1,
            failure_predictions=(),
            component_recommendations=(),
            warnings=(),
            metadata=metadata or {},
        )