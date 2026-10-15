from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RecipeCategory(str, Enum):
    APPS = "apps"
    CAPABILITIES = "capabilities"
    DRIVERS = "drivers"
    FEATURES = "features"
    LANGUAGES = "languages"
    SERVICES = "services"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class RecipeComponent:
    name: str
    category: RecipeCategory
    build_version_min: str = "22000"
    build_version_max: str = "26999"
    dependencies: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    size_mb: int = 0
    description: str = ""
    safe_to_remove: bool = True

    def is_compatible(self, build_version: str) -> bool:
        try:
            v = int(build_version)
            return int(self.build_version_min) <= v <= int(self.build_version_max)
        except ValueError:
            return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "build_version_min": self.build_version_min,
            "build_version_max": self.build_version_max,
            "dependencies": list(self.dependencies),
            "conflicts": list(self.conflicts),
            "size_mb": self.size_mb,
            "description": self.description,
            "safe_to_remove": self.safe_to_remove,
        }


@dataclass(frozen=True, slots=True)
class Recipe:
    name: str
    description: str
    target_build: str
    components: tuple[RecipeComponent, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def total_size_mb(self) -> int:
        return sum(c.size_mb for c in self.components)

    def component_count(self) -> int:
        return len(self.components)

    def categories(self) -> set[RecipeCategory]:
        return {c.category for c in self.components}

    def unsafe_components(self) -> tuple[RecipeComponent, ...]:
        return tuple(c for c in self.components if not c.safe_to_remove)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "target_build": self.target_build,
            "components": [c.to_dict() for c in self.components],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Recipe:
        components = tuple(
            RecipeComponent(
                name=c["name"],
                category=RecipeCategory(c["category"]),
                build_version_min=c.get("build_version_min", "22000"),
                build_version_max=c.get("build_version_max", "26999"),
                dependencies=tuple(c.get("dependencies", ())),
                conflicts=tuple(c.get("conflicts", ())),
                size_mb=c.get("size_mb", 0),
                description=c.get("description", ""),
                safe_to_remove=c.get("safe_to_remove", True),
            )
            for c in data.get("components", [])
        )
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            target_build=data["target_build"],
            components=components,
            metadata=data.get("metadata", {}),
        )