from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from app.models.answer_file import (
    AnswerFileValidation,
    ValidationIssue,
    ValidationSeverity,
    PassName,
)

UNATTEND_NS = "urn:schemas-microsoft-com:unattend"

REQUIRED_PASSES = (
    PassName.WINDOWS_PE,
    PassName.SPECULATE,
    PassName.OOBE_SYSTEM,
)

PRODUCT_KEY_XPATHS = (
    f".//{{{UNATTEND_NS}}}ProductKey",
    f".//{{{UNATTEND_NS}}}ProductKey/{{{UNATTEND_NS}}}Key",
    f".//{{{UNATTEND_NS}}}UserData/{{{UNATTEND_NS}}}ProductKey",
)

LOCALE_SETTINGS = (
    "InputLocale",
    "SystemLocale",
    "UILanguage",
    "UserLocale",
)
TIMEZONE_PATTERN = re.compile(r"^[A-Za-z ]+$")


def _ns(tag: str) -> str:
    return f"{{{UNATTEND_NS}}}{tag}"


@dataclass(frozen=True, slots=True)
class ValidationContext:
    root: ET.Element


def validate_product_key(context: ValidationContext) -> list[ValidationIssue]:
    issues = []
    found = False

    for xpath in PRODUCT_KEY_XPATHS:
        elems = context.root.findall(xpath)
        for elem in elems:
            if elem.text and elem.text.strip():
                found = True
                break
        if found:
            break

    if not found:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MISSING_PRODUCT_KEY",
                message="Cannot read the <ProductKey> setting from the unattended response file",
                xpath=" / ".join(PRODUCT_KEY_XPATHS),
                fix_suggestion="Add a valid ProductKey in the windowsPE pass (for Windows Setup) or oobeSystem pass (for OOBE). Use a generic key or provide a valid volume license key.",
            )
        )

    return issues


def validate_locale_consistency(context: ValidationContext) -> list[ValidationIssue]:
    issues = []
    locales: dict[str, set[str]] = {}

    for setting in LOCALE_SETTINGS:
        xpath = f".//{_ns(setting)}"
        elems = context.root.findall(xpath)
        for elem in elems:
            if elem.text:
                locales.setdefault(setting, set()).add(elem.text.strip())

    for setting, values in locales.items():
        if len(values) > 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="LOCALE_MISMATCH",
                    message=f"Multiple {setting} values found: {', '.join(sorted(values))}",
                    xpath=f".//{_ns(setting)}",
                    fix_suggestion=f"Ensure all {setting} entries use the same locale (e.g., en-US).",
                )
            )

    return issues


def validate_timezone(context: ValidationContext) -> list[ValidationIssue]:
    issues = []
    elems = context.root.findall(f".//{_ns('TimeZone')}")
    for elem in elems:
        if elem.text and not TIMEZONE_PATTERN.match(elem.text.strip()):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="INVALID_TIMEZONE",
                    message=f"TimeZone value '{elem.text}' may not be a valid Windows timezone ID",
                    xpath=f".//{_ns('TimeZone')}",
                    fix_suggestion="Use standard Windows timezone IDs (e.g., 'Pacific Standard Time', 'UTC', 'Eastern Standard Time'). See Microsoft timezone list.",
                )
            )
    return issues


def validate_passes(context: ValidationContext) -> tuple[list[ValidationIssue], tuple[PassName, ...]]:
    issues = []
    found_passes = set()

    settings_xpath = f".//{_ns('settings')}"
    for settings_elem in context.root.findall(settings_xpath):
        pass_attr = settings_elem.get("pass")
        if pass_attr:
            for pn in PassName:
                if pn.value == pass_attr:
                    found_passes.add(pn)
                    break

    for required in REQUIRED_PASSES:
        if required not in found_passes:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="MISSING_PASS",
                    message=f"Recommended pass '{required.value}' not found in answer file",
                    xpath=f".//{_ns('settings')}[@pass='{required.value}']",
                    fix_suggestion=f"Add {required.value} pass for proper deployment flow.",
                )
            )

    return issues, tuple(sorted(found_passes, key=lambda p: p.value))


def validate_components(context: ValidationContext) -> tuple[list[ValidationIssue], tuple[str, ...]]:
    issues = []
    components = set()

    for elem in context.root.iter():
        tag = elem.tag or ""
        # Remove namespace from tag for comparison
        local_tag = tag.split("}")[-1] if "}" in tag else tag

        if local_tag == "component":
            name_attr = elem.get("name")
            if name_attr and "Microsoft-Windows-" in name_attr:
                components.add(name_attr)

                processor_attr = elem.get("processorArchitecture")
                public_key_attr = elem.get("publicKeyToken")
                if processor_attr and public_key_attr:
                    components.add(f"{name_attr} ({processor_attr})")

    return issues, tuple(sorted(components))


def validate_xml_wellformedness(xml_content: str) -> list[ValidationIssue]:
    issues = []
    try:
        ET.fromstring(xml_content)
    except ET.ParseError as e:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="XML_PARSE_ERROR",
                message=f"XML is not well-formed: {e}",
                line=getattr(e, "lineno", 0),
                fix_suggestion="Fix XML syntax error. Check for unclosed tags, invalid characters, or encoding issues.",
            )
        )
    return issues


def validate_autounattend(xml_content: str) -> AnswerFileValidation:
    all_issues = []
    components_referenced = ()
    passes_found = ()

    wellformed_issues = validate_xml_wellformedness(xml_content)
    all_issues.extend(wellformed_issues)

    if not wellformed_issues:
        try:
            root = ET.fromstring(xml_content)
            context = ValidationContext(root=root)

            all_issues.extend(validate_product_key(context))
            all_issues.extend(validate_locale_consistency(context))
            all_issues.extend(validate_timezone(context))

            pass_issues, passes_found = validate_passes(context)
            all_issues.extend(pass_issues)

            comp_issues, components_referenced = validate_components(context)
            all_issues.extend(comp_issues)

        except Exception as e:
            all_issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="VALIDATION_ERROR",
                    message=f"Unexpected validation error: {e}",
                    fix_suggestion="Check answer file structure and try again.",
                )
            )

    has_errors = any(i.severity == ValidationSeverity.ERROR for i in all_issues)
    return AnswerFileValidation(
        valid=not has_errors,
        issues=tuple(all_issues),
        passes_found=passes_found,
        components_referenced=components_referenced,
        metadata={"xml_size": len(xml_content)},
    )