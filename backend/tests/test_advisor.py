from __future__ import annotations

import pytest

from app.models.recipe import RecipeCategory
from app.services.advisor import (
    get_component_database,
    recommend_components,
    ComponentDatabase,
    ComponentInfo,
)


def test_component_database_loads():
    db = get_component_database()
    assert isinstance(db, ComponentDatabase)
    assert len(db.components) > 20


def test_get_component_by_name():
    db = get_component_database()
    edge = db.get("Microsoft.Edge")
    assert edge is not None
    assert edge.name == "Microsoft.Edge"
    assert edge.category == RecipeCategory.APPS
    assert edge.safe_to_remove is True


def test_get_nonexistent_component():
    db = get_component_database()
    result = db.get("NonExistent.Component")
    assert result is None


def test_get_by_category():
    db = get_component_database()
    apps = db.get_by_category(RecipeCategory.APPS, "26100")
    assert len(apps) > 0
    for app in apps:
        assert app.category == RecipeCategory.APPS
        assert app.is_available_for_build("26100")


def test_get_all_for_build():
    db = get_component_database()
    all_26100 = db.get_all_for_build("26100")
    all_22000 = db.get_all_for_build("22000")
    assert len(all_26100) >= len(all_22000)


def test_check_dependencies():
    db = get_component_database()
    # Store depends on EdgeWebView
    missing = db.check_dependencies({"Microsoft.Store"})
    assert "Microsoft.EdgeWebView" in missing

    # Edge has no dependencies
    missing = db.check_dependencies({"Microsoft.Edge"})
    assert len(missing) == 0


def test_check_conflicts():
    db = get_component_database()
    # No conflicts in base set
    conflicts = db.check_conflicts({"Microsoft.Edge", "Microsoft.Store"})
    assert len(conflicts) == 0


def test_recommend_components_basic():
    recs = recommend_components("26100")
    assert len(recs) > 0

    # All should be safe to remove (by default)
    for rec in recs:
        assert rec.recommended is True or rec.risk_score > 0.5
        assert rec.component_name
        assert rec.category


def test_recommend_components_with_categories():
    recs = recommend_components("26100", categories=(RecipeCategory.APPS,))
    for rec in recs:
        assert rec.category == "apps"


def test_recommend_components_include_unsafe():
    recs_safe = recommend_components("26100", include_unsafe=False)
    recs_all = recommend_components("26100", include_unsafe=True)
    assert len(recs_all) >= len(recs_safe)


def test_recommend_components_risk_ordering():
    recs = recommend_components("26100")
    risk_scores = [r.risk_score for r in recs]
    # Should be sorted by risk_score ascending
    assert risk_scores == sorted(risk_scores)


def test_recommend_components_specific_build():
    recs_22000 = recommend_components("22000")
    recs_26100 = recommend_components("26100")

    # Some components only available in newer builds (e.g., Teams)
    teams_22000 = next((r for r in recs_22000 if r.component_name == "Microsoft.Teams"), None)
    teams_26100 = next((r for r in recs_26100 if r.component_name == "Microsoft.Teams"), None)
    assert teams_22000 is None
    assert teams_26100 is not None


def test_component_info_structure():
    db = get_component_database()
    edge = db.get("Microsoft.Edge")
    assert edge is not None
    assert edge.size_mb > 0
    assert isinstance(edge.dependencies, tuple)
    assert isinstance(edge.conflicts, tuple)
    assert isinstance(edge.provides, tuple)
    assert isinstance(edge.required_by, tuple)