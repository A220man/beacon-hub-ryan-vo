from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

from app.models.recipe import Recipe, RecipeComponent, RecipeCategory
from app.models.analysis import (
    AnalysisResult,
    FailurePrediction,
    ComponentRecommendation,
    RiskLevel,
    FailureType,
)


@dataclass(frozen=True, slots=True)
class FeatureVector:
    component_count: int
    unsafe_component_count: int
    category_count: int
    total_size_mb: int
    target_build: int
    has_apps: bool
    has_drivers: bool
    has_services: bool
    has_system: bool
    dependency_violations: int
    conflict_count: int

    def to_array(self) -> list[float]:
        return [
            float(self.component_count),
            float(self.unsafe_component_count),
            float(self.category_count),
            float(self.total_size_mb),
            float(self.target_build),
            1.0 if self.has_apps else 0.0,
            1.0 if self.has_drivers else 0.0,
            1.0 if self.has_services else 0.0,
            1.0 if self.has_system else 0.0,
            float(self.dependency_violations),
            float(self.conflict_count),
        ]


class DeterministicPredictor:
    def __init__(self, seed: str = "beacon-hub-v1"):
        self.seed = seed

    def _hash_feature(self, feature_name: str, value: float) -> float:
        h = hashlib.blake2b(f"{self.seed}:{feature_name}:{value}".encode(), digest_size=8).digest()
        return int.from_bytes(h, "big") / (2**64 - 1)

    def predict_dism_failure(self, features: FeatureVector) -> FailurePrediction:
        base_risk = 0.15
        base_risk += 0.02 * features.component_count
        base_risk += 0.1 * features.unsafe_component_count
        base_risk += 0.05 * features.dependency_violations
        base_risk += 0.03 * features.conflict_count
        if features.has_drivers:
            base_risk += 0.1
        if features.has_services:
            base_risk += 0.08
        if features.target_build >= 26000:
            base_risk += 0.12

        prob = min(max(base_risk + self._hash_feature("dism", features.target_build) * 0.1, 0.0), 1.0)
        risk_level = self._prob_to_risk(prob)

        return FailurePrediction(
            failure_type=FailureType.DISM_PENDING_OPERATIONS,
            probability=prob,
            risk_level=risk_level,
            description=(
                "DISM 0x800f0806: The operation could not be completed due to pending operations. "
                "Common when removing components with pending servicing actions."
            ),
            evidence=[
                f"Component count: {features.component_count}",
                f"Unsafe components: {features.unsafe_component_count}",
                f"Target build: {features.target_build}",
            ],
            mitigation="Stage removals in correct pass order; ensure no pending.xml exists before cleanup phase.",
        )

    def predict_registry_failure(self, features: FeatureVector) -> FailurePrediction:
        base_risk = 0.08
        base_risk += 0.05 * features.unsafe_component_count
        base_risk += 0.04 * features.conflict_count
        if features.has_system:
            base_risk += 0.15
        if features.target_build >= 26000:
            base_risk += 0.1

        prob = min(max(base_risk + self._hash_feature("registry", features.target_build) * 0.08, 0.0), 1.0)
        risk_level = self._prob_to_risk(prob)

        return FailurePrediction(
            failure_type=FailureType.REGISTRY_ACCESS_DENIED,
            probability=prob,
            risk_level=risk_level,
            description=(
                "Offline registry access denied (Error 5). Cannot set registry values on mounted image. "
                "Typically occurs when modifying SearchSettings or other protected keys."
            ),
            evidence=[
                f"System components: {features.has_system}",
                f"Conflicts: {features.conflict_count}",
                f"Target build: {features.target_build}",
            ],
            mitigation="Run as Administrator; verify image is not in use; check WIM mount permissions.",
        )

    def predict_adk_mismatch(self, features: FeatureVector) -> FailurePrediction:
        prob = 0.0
        if features.target_build >= 26000:
            prob = 0.25 + self._hash_feature("adk", features.target_build) * 0.15
        elif features.target_build >= 25000:
            prob = 0.1 + self._hash_feature("adk", features.target_build) * 0.1

        risk_level = self._prob_to_risk(prob)

        return FailurePrediction(
            failure_type=FailureType.ADK_VERSION_MISMATCH,
            probability=prob,
            risk_level=risk_level,
            description=(
                "Installed ADK Deployment Tools version is older than required for target image build. "
                "Windows 10 hosts building Windows 11 24H2/26H2 need updated ADK."
            ),
            evidence=[
                f"Target build: {features.target_build}",
                "ADK version check required at build time",
            ],
            mitigation="Install Windows ADK matching or newer than target image build version.",
        )

    def _prob_to_risk(self, prob: float) -> RiskLevel:
        if prob >= 0.7:
            return RiskLevel.CRITICAL
        if prob >= 0.5:
            return RiskLevel.HIGH
        if prob >= 0.3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


def extract_features(recipe: Recipe) -> FeatureVector:
    target_build = int(recipe.target_build) if recipe.target_build.isdigit() else 26100
    categories = recipe.categories()

    component_names = {c.name for c in recipe.components}
    dep_violations = 0
    conflict_count = 0

    for comp in recipe.components:
        for dep in comp.dependencies:
            if dep not in component_names:
                dep_violations += 1
        for conflict in comp.conflicts:
            if conflict in component_names:
                conflict_count += 1

    return FeatureVector(
        component_count=recipe.component_count(),
        unsafe_component_count=len(recipe.unsafe_components()),
        category_count=len(categories),
        total_size_mb=recipe.total_size_mb(),
        target_build=target_build,
        has_apps=RecipeCategory.APPS in categories,
        has_drivers=RecipeCategory.DRIVERS in categories,
        has_services=RecipeCategory.SERVICES in categories,
        has_system=RecipeCategory.SYSTEM in categories,
        dependency_violations=dep_violations,
        conflict_count=conflict_count,
    )


def analyze_recipe(recipe: Recipe) -> AnalysisResult:
    features = extract_features(recipe)
    predictor = DeterministicPredictor()

    predictions = (
        predictor.predict_dism_failure(features),
        predictor.predict_registry_failure(features),
        predictor.predict_adk_mismatch(features),
    )

    component_recs = tuple(
        ComponentRecommendation(
            component_name=comp.name,
            category=comp.category.value,
            recommended=comp.safe_to_remove and all(d in component_names for d in comp.dependencies),
            reason="Safe removal" if comp.safe_to_remove else "Marked unsafe in component database",
            risk_score=0.2 if comp.safe_to_remove else 0.8,
            dependencies_satisfied=all(d in component_names for d in comp.dependencies),
            conflicts=tuple(c for c in comp.conflicts if c in component_names),
        )
        for comp in recipe.components
    )

    max_prob = max(p.probability for p in predictions)
    overall_risk = RiskLevel.LOW
    if max_prob >= 0.7:
        overall_risk = RiskLevel.CRITICAL
    elif max_prob >= 0.5:
        overall_risk = RiskLevel.HIGH
    elif max_prob >= 0.3:
        overall_risk = RiskLevel.MEDIUM

    warnings = []
    if features.dependency_violations > 0:
        warnings.append(f"{features.dependency_violations} missing dependencies detected")
    if features.conflict_count > 0:
        warnings.append(f"{features.conflict_count} component conflicts detected")
    if features.target_build >= 26000:
        warnings.append("Target build 26000+ requires preview ADK or newer host")

    return AnalysisResult(
        recipe_name=recipe.name,
        target_build=recipe.target_build,
        analyzed_at=AnalysisResult.create_low_risk("", "").analyzed_at,
        overall_risk=overall_risk,
        risk_score=max_prob,
        failure_predictions=predictions,
        component_recommendations=component_recs,
        warnings=tuple(warnings),
        metadata={
            "feature_vector": {
                "component_count": features.component_count,
                "unsafe_count": features.unsafe_component_count,
                "total_size_mb": features.total_size_mb,
            }
        },
    )