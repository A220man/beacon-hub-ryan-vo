from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PassName(str, Enum):
    WINDOWS_PE = "windowsPE"
    OFFLINE_SERVICING = "offlineServicing"
    GENERALIZE = "generalize"
    SPECULATE = "specialize"
    AUDIT_SYSTEM = "auditSystem"
    AUDIT_USER = "auditUser"
    OOBE_SYSTEM = "oobeSystem"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: ValidationSeverity
    code: str
    message: str
    xpath: str = ""
    line: int = 0
    fix_suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "xpath": self.xpath,
            "line": self.line,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass(frozen=True, slots=True)
class AnswerFileValidation:
    valid: bool
    issues: tuple[ValidationIssue, ...]
    passes_found: tuple[PassName, ...]
    components_referenced: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.ERROR)

    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity == ValidationSeverity.WARNING)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [i.to_dict() for i in self.issues],
            "passes_found": [p.value for p in self.passes_found],
            "components_referenced": list(self.components_referenced),
            "metadata": self.metadata,
        }