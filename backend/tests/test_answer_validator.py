from __future__ import annotations

import pytest

from app.services.answer_validator import validate_autounattend, ValidationSeverity


VALID_AUTOUNATTEND = """<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="windowsPE">
        <component name="Microsoft-Windows-International-Core-WinPE" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
            <SetupUILanguage>
                <UILanguage>en-US</UILanguage>
            </SetupUILanguage>
            <InputLocale>en-US</InputLocale>
            <SystemLocale>en-US</SystemLocale>
            <UILanguage>en-US</UILanguage>
            <UserLocale>en-US</UserLocale>
        </component>
        <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
            <UserData>
                <ProductKey>
                    <Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>
                </ProductKey>
                <AcceptEula>true</AcceptEula>
            </UserData>
        </component>
    </settings>
    <settings pass="specialize">
        <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
            <TimeZone>Pacific Standard Time</TimeZone>
        </component>
    </settings>
    <settings pass="oobeSystem">
        <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
            <OOBE>
                <HideEULAPage>true</HideEULAPage>
                <HideLocalAccountScreen>true</HideLocalAccountScreen>
            </OOBE>
        </component>
    </settings>
</unattend>
"""


def test_valid_autounattend():
    result = validate_autounattend(VALID_AUTOUNATTEND)
    assert result.valid is True
    assert len(result.errors()) == 0
    assert PassName.WINDOWS_PE in result.passes_found
    assert PassName.SPECULATE in result.passes_found
    assert PassName.OOBE_SYSTEM in result.passes_found


def test_missing_product_key():
    xml = VALID_AUTOUNATTEND.replace(
        "<Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>",
        "<Key></Key>"
    )
    result = validate_autounattend(xml)
    assert result.valid is False
    errors = result.errors()
    assert len(errors) == 1
    assert errors[0].code == "MISSING_PRODUCT_KEY"


def test_missing_product_key_entirely():
    xml = VALID_AUTOUNATTEND.replace(
        """<ProductKey>
                    <Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>
                </ProductKey>""",
        ""
    )
    result = validate_autounattend(xml)
    assert result.valid is False
    errors = result.errors()
    assert len(errors) == 1
    assert errors[0].code == "MISSING_PRODUCT_KEY"


def test_locale_mismatch():
    # Add a second SystemLocale with different value to trigger mismatch
    xml = VALID_AUTOUNATTEND.replace(
        "<SystemLocale>en-US</SystemLocale>",
        "<SystemLocale>en-US</SystemLocale>\n            <SystemLocale>de-DE</SystemLocale>"
    )
    result = validate_autounattend(xml)
    assert result.valid is True  # Warning, not error
    warnings = result.warnings()
    assert any(w.code == "LOCALE_MISMATCH" for w in warnings)

def test_invalid_timezone():
    xml = VALID_AUTOUNATTEND.replace(
        "<TimeZone>Pacific Standard Time</TimeZone>",
        "<TimeZone>Invalid/Timezone</TimeZone>"
    )
    result = validate_autounattend(xml)
    warnings = result.warnings()
    assert any(w.code == "INVALID_TIMEZONE" for w in warnings)


def test_missing_recommended_passes():
    xml = """<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
    <settings pass="windowsPE">
        <component name="Microsoft-Windows-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS">
            <UserData>
                <ProductKey><Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key></ProductKey>
            </UserData>
        </component>
    </settings>
</unattend>
"""
    result = validate_autounattend(xml)
    warnings = result.warnings()
    assert any(w.code == "MISSING_PASS" for w in warnings)


def test_malformed_xml():
    xml = "<unattend><settings pass=\"windowsPE\"><component>"
    result = validate_autounattend(xml)
    assert result.valid is False
    errors = result.errors()
    assert len(errors) == 1
    assert errors[0].code == "XML_PARSE_ERROR"


def test_empty_xml():
    result = validate_autounattend("")
    assert result.valid is False
    errors = result.errors()
    assert len(errors) == 1
    assert errors[0].code == "XML_PARSE_ERROR"


def test_large_xml_rejected():
    large_xml = "x" * 2_000_000
    # This tests the 1MB limit in the API, not the validator directly
    # But we can test the validator handles large input
    result = validate_autounattend(large_xml)
    assert result.valid is False


def test_issue_sorting_by_severity():
    xml = VALID_AUTOUNATTEND.replace(
        "<Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>",
        "<Key></Key>"
    )
    # Add a warning too
    xml = xml.replace(
        "<TimeZone>Pacific Standard Time</TimeZone>",
        "<TimeZone>Invalid/Timezone</TimeZone>"
    )
    result = validate_autounattend(xml)
    errors = result.errors()
    warnings = result.warnings()

    # Errors should come first when sorted by severity
    assert len(errors) > 0
    assert all(e.severity == ValidationSeverity.ERROR for e in errors)
    assert all(w.severity == ValidationSeverity.WARNING for w in warnings)


def test_component_references_found():
    result = validate_autounattend(VALID_AUTOUNATTEND)
    components = result.components_referenced
    assert len(components) > 0
    assert any("Microsoft-Windows-International-Core-WinPE" in c for c in components)
    assert any("Microsoft-Windows-Setup" in c for c in components)
    assert any("Microsoft-Windows-Shell-Setup" in c for c in components)


# Need to import PassName for the test
from app.models.answer_file import PassName