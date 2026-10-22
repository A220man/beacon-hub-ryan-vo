from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import require_viewer
from app.models.recipe import Recipe, RecipeCategory
from app.models.analysis import AnalysisResult
from app.services.predictor import analyze_recipe
from app.services.advisor import recommend_components, get_component_database, ComponentInfo

router = APIRouter(prefix="/api/v1/analyze", tags=["analysis"], dependencies=[Depends(require_viewer)])



class AnalyzeRecipeRequest(BaseModel):
    recipe: dict
    target_build: str = Field(default="26100", pattern=r"^\d{5}$")


class AnalyzeRecipeResponse(BaseModel):
    analysis: dict


@router.post("/recipe", response_model=AnalyzeRecipeResponse)
async def analyze_recipe_endpoint(request: AnalyzeRecipeRequest) -> AnalyzeRecipeResponse:
    try:
        recipe = Recipe.from_dict(request.recipe)
        if recipe.target_build != request.target_build:
            recipe = Recipe(
                name=recipe.name,
                description=recipe.description,
                target_build=request.target_build,
                components=recipe.components,
                metadata=recipe.metadata,
            )
        result = analyze_recipe(recipe)
        return AnalyzeRecipeResponse(analysis=result.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to analyze recipe: {e}",
        ) from e


class ComponentAdvisorRequest(BaseModel):
    target_build: str = Field(default="26100", pattern=r"^\d{5}$")
    categories: list[str] | None = None
    include_unsafe: bool = False


class ComponentAdvisorResponse(BaseModel):
    components: list[dict]
    target_build: str


@router.post("/advisor/components", response_model=ComponentAdvisorResponse)
async def advisor_components(request: ComponentAdvisorRequest) -> ComponentAdvisorResponse:
    try:
        categories = None
        if request.categories:
            categories = tuple(RecipeCategory(c) for c in request.categories)

        recommendations = recommend_components(
            target_build=request.target_build,
            categories=categories,
            include_unsafe=request.include_unsafe,
        )
        return ComponentAdvisorResponse(
            components=[r.to_dict() for r in recommendations],
            target_build=request.target_build,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {e}",
        ) from e


class ComponentInfoResponse(BaseModel):
    name: str
    category: str
    description: str
    size_mb: int
    dependencies: list[str]
    conflicts: list[str]
    safe_to_remove: bool
    min_build: str
    max_build: str
    provides: list[str]
    required_by: list[str]


class ComponentDatabaseResponse(BaseModel):
    components: list[ComponentInfoResponse]
    target_build: str
    total_count: int


@router.get("/advisor/database", response_model=ComponentDatabaseResponse)
async def advisor_database(target_build: str = "26100") -> ComponentDatabaseResponse:
    try:
        db = get_component_database()
        available = db.get_all_for_build(target_build)
        return ComponentDatabaseResponse(
            components=[
                ComponentInfoResponse(
                    name=c.name,
                    category=c.category.value,
                    description=c.description,
                    size_mb=c.size_mb,
                    dependencies=list(c.dependencies),
                    conflicts=list(c.conflicts),
                    safe_to_remove=c.safe_to_remove,
                    min_build=c.min_build,
                    max_build=c.max_build,
                    provides=list(c.provides),
                    required_by=list(c.required_by),
                )
                for c in available
            ],
            target_build=target_build,
            total_count=len(available),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get component database: {e}",
        ) from e