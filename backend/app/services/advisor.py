from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.recipe import RecipeCategory
from app.models.analysis import ComponentRecommendation


@dataclass(frozen=True, slots=True)
class ComponentInfo:
    name: str
    category: RecipeCategory
    description: str
    size_mb: int
    dependencies: tuple[str, ...]
    conflicts: tuple[str, ...]
    safe_to_remove: bool
    min_build: str
    max_build: str
    provides: tuple[str, ...] = ()
    required_by: tuple[str, ...] = ()

    def is_available_for_build(self, build: str) -> bool:
        try:
            v = int(build)
            return int(self.min_build) <= v <= int(self.max_build)
        except ValueError:
            return True


@dataclass(frozen=True, slots=True)
class ComponentDatabase:
    components: dict[str, ComponentInfo]

    def get(self, name: str) -> ComponentInfo | None:
        return self.components.get(name)

    def get_by_category(self, category: RecipeCategory, build: str) -> tuple[ComponentInfo, ...]:
        return tuple(
            c for c in self.components.values()
            if c.category == category and c.is_available_for_build(build)
        )

    def get_all_for_build(self, build: str) -> tuple[ComponentInfo, ...]:
        return tuple(c for c in self.components.values() if c.is_available_for_build(build))

    def check_dependencies(self, component_names: set[str]) -> tuple[str, ...]:
        missing = set()
        for name in component_names:
            comp = self.components.get(name)
            if comp:
                for dep in comp.dependencies:
                    if dep not in component_names:
                        missing.add(dep)
        return tuple(sorted(missing))

    def check_conflicts(self, component_names: set[str]) -> tuple[tuple[str, str], ...]:
        conflicts = set()
        for name in component_names:
            comp = self.components.get(name)
            if comp:
                for conflict in comp.conflicts:
                    if conflict in component_names:
                        pair = tuple(sorted((name, conflict)))
                        conflicts.add(pair)
        return tuple(sorted(conflicts))


_KNOWN_COMPONENTS: dict[str, ComponentInfo] = {
    # Apps
    "Microsoft.Edge": ComponentInfo(
        name="Microsoft.Edge",
        category=RecipeCategory.APPS,
        description="Microsoft Edge web browser",
        size_mb=180,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Microsoft.EdgeWebView": ComponentInfo(
        name="Microsoft.EdgeWebView",
        category=RecipeCategory.APPS,
        description="WebView2 runtime for Edge-based apps",
        size_mb=95,
        dependencies=(),
        conflicts=(),
        safe_to_remove=False,
        min_build="22000",
        max_build="26999",
        required_by=("Microsoft.Store", "Microsoft.Teams"),
    ),
    "Microsoft.Store": ComponentInfo(
        name="Microsoft.Store",
        category=RecipeCategory.APPS,
        description="Microsoft Store app",
        size_mb=45,
        dependencies=("Microsoft.EdgeWebView",),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Microsoft.XboxApp": ComponentInfo(
        name="Microsoft.XboxApp",
        category=RecipeCategory.APPS,
        description="Xbox Game Bar and app",
        size_mb=35,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Microsoft.Teams": ComponentInfo(
        name="Microsoft.Teams",
        category=RecipeCategory.APPS,
        description="Microsoft Teams consumer app",
        size_mb=65,
        dependencies=("Microsoft.EdgeWebView",),
        conflicts=(),
        safe_to_remove=True,
        min_build="22621",
        max_build="26999",
    ),
    "Microsoft.OfficeHub": ComponentInfo(
        name="Microsoft.OfficeHub",
        category=RecipeCategory.APPS,
        description="Office Hub/shortcuts",
        size_mb=12,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Microsoft.YourPhone": ComponentInfo(
        name="Microsoft.YourPhone",
        category=RecipeCategory.APPS,
        description="Phone Link app",
        size_mb=28,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Microsoft.ScreenSketch": ComponentInfo(
        name="Microsoft.ScreenSketch",
        category=RecipeCategory.APPS,
        description="Snipping Tool / Screen Sketch",
        size_mb=8,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Microsoft.Paint": ComponentInfo(
        name="Microsoft.Paint",
        category=RecipeCategory.APPS,
        description="Paint app",
        size_mb=15,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Microsoft.Notepad": ComponentInfo(
        name="Microsoft.Notepad",
        category=RecipeCategory.APPS,
        description="Notepad app",
        size_mb=6,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    # Capabilities
    "Print.Fax.Scan": ComponentInfo(
        name="Print.Fax.Scan",
        category=RecipeCategory.CAPABILITIES,
        description="Print, Fax, and Scan capabilities",
        size_mb=25,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Windows.Fax": ComponentInfo(
        name="Windows.Fax",
        category=RecipeCategory.CAPABILITIES,
        description="Windows Fax and Scan",
        size_mb=18,
        dependencies=("Print.Fax.Scan",),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "XPS.Viewer": ComponentInfo(
        name="XPS.Viewer",
        category=RecipeCategory.CAPABILITIES,
        description="XPS Document Viewer",
        size_mb=4,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Math.Recognizer": ComponentInfo(
        name="Math.Recognizer",
        category=RecipeCategory.CAPABILITIES,
        description="Math Input Panel / Recognizer",
        size_mb=12,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    # Drivers
    "Driver.Wifi": ComponentInfo(
        name="Driver.Wifi",
        category=RecipeCategory.DRIVERS,
        description="Generic WiFi drivers",
        size_mb=15,
        dependencies=(),
        conflicts=(),
        safe_to_remove=False,
        min_build="22000",
        max_build="26999",
    ),
    "Driver.Bluetooth": ComponentInfo(
        name="Driver.Bluetooth",
        category=RecipeCategory.DRIVERS,
        description="Bluetooth driver stack",
        size_mb=12,
        dependencies=(),
        conflicts=(),
        safe_to_remove=False,
        min_build="22000",
        max_build="26999",
    ),
    "Driver.Printer": ComponentInfo(
        name="Driver.Printer",
        category=RecipeCategory.DRIVERS,
        description="Generic printer drivers",
        size_mb=45,
        dependencies=("Print.Fax.Scan",),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Driver.Scanner": ComponentInfo(
        name="Driver.Scanner",
        category=RecipeCategory.DRIVERS,
        description="Scanner drivers (WIA/TWAIN)",
        size_mb=8,
        dependencies=("Print.Fax.Scan",),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    # Features
    "Telnet.Client": ComponentInfo(
        name="Telnet.Client",
        category=RecipeCategory.FEATURES,
        description="Telnet client",
        size_mb=2,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "TFTP.Client": ComponentInfo(
        name="TFTP.Client",
        category=RecipeCategory.FEATURES,
        description="TFTP client",
        size_mb=1,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "IIS.WebServer": ComponentInfo(
        name="IIS.WebServer",
        category=RecipeCategory.FEATURES,
        description="Internet Information Services",
        size_mb=35,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "SMB1.Protocol": ComponentInfo(
        name="SMB1.Protocol",
        category=RecipeCategory.FEATURES,
        description="SMB 1.0/CIFS file sharing support",
        size_mb=3,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "PowerShell.ISE": ComponentInfo(
        name="PowerShell.ISE",
        category=RecipeCategory.FEATURES,
        description="PowerShell ISE (legacy)",
        size_mb=8,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    # Languages
    "LanguagePack.Extra": ComponentInfo(
        name="LanguagePack.Extra",
        category=RecipeCategory.LANGUAGES,
        description="Additional language packs (non-system)",
        size_mb=200,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Handwriting.Recognition": ComponentInfo(
        name="Handwriting.Recognition",
        category=RecipeCategory.LANGUAGES,
        description="Handwriting recognition for extra languages",
        size_mb=85,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "Speech.Recognition": ComponentInfo(
        name="Speech.Recognition",
        category=RecipeCategory.LANGUAGES,
        description="Speech recognition for extra languages",
        size_mb=120,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    # Services
    "DiagTrack": ComponentInfo(
        name="DiagTrack",
        category=RecipeCategory.SERVICES,
        description="Connected User Experiences and Telemetry",
        size_mb=5,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "WSearch": ComponentInfo(
        name="WSearch",
        category=RecipeCategory.SERVICES,
        description="Windows Search indexer",
        size_mb=12,
        dependencies=(),
        conflicts=(),
        safe_to_remove=False,
        min_build="22000",
        max_build="26999",
        required_by=("Microsoft.Store", "Cortana"),
    ),
    "SysMain": ComponentInfo(
        name="SysMain",
        category=RecipeCategory.SERVICES,
        description="Superfetch / SysMain",
        size_mb=4,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "RemoteRegistry": ComponentInfo(
        name="RemoteRegistry",
        category=RecipeCategory.SERVICES,
        description="Remote Registry service",
        size_mb=2,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    # System
    "WinRE": ComponentInfo(
        name="WinRE",
        category=RecipeCategory.SYSTEM,
        description="Windows Recovery Environment",
        size_mb=500,
        dependencies=(),
        conflicts=(),
        safe_to_remove=False,
        min_build="22000",
        max_build="26999",
    ),
    "Hibernation": ComponentInfo(
        name="Hibernation",
        category=RecipeCategory.SYSTEM,
        description="Hibernation file (hiberfil.sys)",
        size_mb=0,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
    "PageFile": ComponentInfo(
        name="PageFile",
        category=RecipeCategory.SYSTEM,
        description="System page file management",
        size_mb=0,
        dependencies=(),
        conflicts=(),
        safe_to_remove=False,
        min_build="22000",
        max_build="26999",
    ),
    "CompactOS": ComponentInfo(
        name="CompactOS",
        category=RecipeCategory.SYSTEM,
        description="Compact OS compression",
        size_mb=0,
        dependencies=(),
        conflicts=(),
        safe_to_remove=False,
        min_build="22000",
        max_build="26999",
    ),
    "ReservedStorage": ComponentInfo(
        name="ReservedStorage",
        category=RecipeCategory.SYSTEM,
        description="Reserved storage for updates",
        size_mb=7000,
        dependencies=(),
        conflicts=(),
        safe_to_remove=True,
        min_build="22000",
        max_build="26999",
    ),
}


def get_component_database() -> ComponentDatabase:
    return ComponentDatabase(components=_KNOWN_COMPONENTS.copy())


def recommend_components(
    target_build: str,
    categories: tuple[RecipeCategory, ...] | None = None,
    include_unsafe: bool = False,
) -> tuple[ComponentRecommendation, ...]:
    db = get_component_database()
    available = db.get_all_for_build(target_build)

    if categories:
        available = tuple(c for c in available if c.category in categories)

    recommendations = []
    for comp in available:
        if not include_unsafe and not comp.safe_to_remove:
            continue

        missing_deps = db.check_dependencies({comp.name})
        conflicts = db.check_conflicts({comp.name})

        risk = 0.1
        if not comp.safe_to_remove:
            risk = 0.9
        if missing_deps:
            risk = max(risk, 0.6)
        if conflicts:
            risk = max(risk, 0.7)

        reason = "Safe to remove" if comp.safe_to_remove else "Core system component - removing may break OS"
        if missing_deps:
            reason += f"; missing dependencies: {', '.join(missing_deps)}"
        if conflicts:
            reason += f"; conflicts with: {', '.join(c[1] for c in conflicts)}"

        recommendations.append(
            ComponentRecommendation(
                component_name=comp.name,
                category=comp.category.value,
                recommended=comp.safe_to_remove and not missing_deps and not conflicts,
                reason=reason,
                risk_score=risk,
                dependencies_satisfied=len(missing_deps) == 0,
                conflicts=tuple(c[1] for c in conflicts),
            )
        )

    return tuple(sorted(recommendations, key=lambda r: r.risk_score))