from __future__ import annotations

import pytest

from app.models.recipe import Recipe, RecipeComponent, RecipeCategory
from app.services.predictor import extract_features, analyze_recipe, DeterministicPredictor, FeatureVector


def test_feature_extraction():
    recipe = Recipe(
        name="Test Recipe",
        description="Test",
        target_build="26100",
        components=(
            RecipeComponent(
                name="Component1",
                category=RecipeCategory.APPS,
                safe_to_remove=True,
                size_mb=10,
            ),
            RecipeComponent(
                name="Component2",
                category=RecipeCategory.SERVICES,
                safe_to_remove=False,
                size_mb=20,
            ),
        ),
    )

    features = extract_features(recipe)
    assert features.component_count == 2
    assert features.unsafe_component_count == 1
    assert features.category_count == 2
    assert features.total_size_mb == 30
    assert features.target_build == 26100
    assert features.has_apps is True
    assert features.has_services is True
    assert features.has_drivers is False
    assert features.has_system is False


def test_feature_extraction_with_dependencies():
    recipe = Recipe(
        name="Test Recipe",
        description="Test",
        target_build="26100",
        components=(
            RecipeComponent(
                name="Component1",
                category=RecipeCategory.APPS,
                safe_to_remove=True,
                dependencies=("MissingDep",),
            ),
            RecipeComponent(
                name="Component2",
                category=RecipeCategory.SERVICES,
                safe_to_remove=True,
                conflicts=("Component1",),
            ),
        ),
    )

    features = extract_features(recipe)
    assert features.dependency_violations == 1
    assert features.conflict_count == 1


def test_deterministic_predictor_dism():
    predictor = DeterministicPredictor()
    features = FeatureVector(
        component_count=10,
        unsafe_component_count=2,
        category_count=3,
        total_size_mb=500,
        target_build=26100,
        has_apps=True,
        has_drivers=False,
        has_services=True,
        has_system=False,
        dependency_violations=0,
        conflict_count=0,
    )

    pred = predictor.predict_dism_failure(features)
    assert pred.failure_type.value == "dism_pending_operations"
    assert 0.0 <= pred.probability <= 1.0
    assert pred.risk_level.value in ("low", "medium", "high", "critical")
    assert len(pred.evidence) > 0
    assert len(pred.mitigation) > 0


def test_deterministic_predictor_registry():
    predictor = DeterministicPredictor()
    features = FeatureVector(
        component_count=5,
        unsafe_component_count=1,
        category_count=2,
        total_size_mb=100,
        target_build=26100,
        has_apps=False,
        has_drivers=False,
        has_services=False,
        has_system=True,
        dependency_violations=0,
        conflict_count=0,
    )

    pred = predictor.predict_registry_failure(features)
    assert pred.failure_type.value == "registry_access_denied"
    assert 0.0 <= pred.probability <= 1.0


def test_deterministic_predictor_adk():
    predictor = DeterministicPredictor()
    features_old = FeatureVector(
        component_count=5,
        unsafe_component_count=0,
        category_count=1,
        total_size_mb=50,
        target_build=22000,
        has_apps=False,
        has_drivers=False,
        has_services=False,
        has_system=False,
        dependency_violations=0,
        conflict_count=0,
    )
    features_new = FeatureVector(
        component_count=5,
        unsafe_component_count=0,
        category_count=1,
        total_size_mb=50,
        target_build=26100,
        has_apps=False,
        has_drivers=False,
        has_services=False,
        has_system=False,
        dependency_violations=0,
        conflict_count=0,
    )

    pred_old = predictor.predict_adk_mismatch(features_old)
    pred_new = predictor.predict_adk_mismatch(features_new)

    assert pred_new.probability >= pred_old.probability


def test_analyze_recipe():
    recipe = Recipe(
        name="Test Recipe",
        description="Test recipe for analysis",
        target_build="26100",
        components=(
            RecipeComponent(
                name="Microsoft.Edge",
                category=RecipeCategory.APPS,
                safe_to_remove=True,
                size_mb=180,
            ),
            RecipeComponent(
                name="DiagTrack",
                category=RecipeCategory.SERVICES,
                safe_to_remove=True,
                size_mb=5,
            ),
        ),
    )

    result = analyze_recipe(recipe)
    assert result.recipe_name == "Test Recipe"
    assert result.target_build == "26100"
    assert result.overall_risk.value in ("low", "medium", "high", "critical")
    assert 0.0 <= result.risk_score <= 1.0
    assert len(result.failure_predictions) == 3
    assert len(result.component_recommendations) == 2

    # Check all failure types present
    failure_types = {p.failure_type for p in result.failure_predictions}
    assert len(failure_types) == 3


def test_analyze_recipe_high_risk():
    recipe = Recipe(
        name="Risky Recipe",
        description="Many unsafe components",
        target_build="26300",
        components=(
            RecipeComponent(
                name="WinRE",
                category=RecipeCategory.SYSTEM,
                safe_to_remove=False,
                size_mb=500,
            ),
            RecipeComponent(
                name="PageFile",
                category=RecipeCategory.SYSTEM,
                safe_to_remove=False,
                size_mb=0,
            ),
            RecipeComponent(
                name="Driver.Wifi",
                category=RecipeCategory.DRIVERS,
                safe_to_remove=False,
                size_mb=15,
            ),
        ),
    )

    result = analyze_recipe(recipe)
    assert result.overall_risk.value in ("high", "critical")
    assert result.risk_score > 0.3


def test_predictor_deterministic():
    predictor = DeterministicPredictor()
    features = FeatureVector(
        component_count=10,
        unsafe_component_count=2,
        category_count=3,
        total_size_mb=500,
        target_build=26100,
        has_apps=True,
        has_drivers=False,
        has_services=True,
        has_system=False,
        dependency_violations=0,
        conflict_count=0,
    )

    pred1 = predictor.predict_dism_failure(features)
    pred2 = predictor.predict_dism_failure(features)

    assert pred1.probability == pred2.probability
    assert pred1.risk_level == pred2.risk_level