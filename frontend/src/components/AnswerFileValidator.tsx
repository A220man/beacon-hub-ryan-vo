import { useState } from "react";
import { validateAutounattend, ValidateAutounattendResponse, ValidationIssue } from "../api/client";
import "./AnswerFileValidator.css";

type FilterSeverity = "all" | "error" | "warning" | "info";

export function AnswerFileValidator() {
  const [xmlContent, setXmlContent] = useState(
    `<?xml version="1.0" encoding="utf-8"?>
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
</unattend>`
  );
  const [result, setResult] = useState<ValidateAutounattendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<FilterSeverity>("all");

  const handleValidate = async () => {
    if (!xmlContent.trim()) {
      setError("XML content is required");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await validateAutounattend(xmlContent);
      setResult(response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setLoading(false);
    }
  };

  const severityColor = (severity: string) => {
    switch (severity) {
      case "error": return "var(--color-error)";
      case "warning": return "var(--color-warning)";
      case "info": return "var(--color-primary)";
      default: return "var(--color-text-muted)";
    }
  };

  const filteredIssues = result?.issues.filter(issue =>
    filterSeverity === "all" || issue.severity === filterSeverity
  ) || [];

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilterSeverity(e.target.value as FilterSeverity);
  };

  return (
    <div className="answer-validator card">
      <h2>Unattended Answer File Validator</h2>
      <p className="description">Validate autounattend.xml for common deployment errors including ProductKey, locale, timezone, and component references.</p>

      <div className="input-section">
        <div className="input-group full-width">
          <label htmlFor="autounattend-xml">autounattend.xml</label>
          <textarea
            id="autounattend-xml"
            value={xmlContent}
            onChange={(e) => setXmlContent(e.target.value)}
            rows={15}
            spellCheck={false}
            placeholder="Paste your autounattend.xml here..."
          />
        </div>

        <button className="btn-primary" onClick={handleValidate} disabled={loading}>
          {loading ? "Validating..." : "Validate Answer File"}
        </button>
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {result && (
        <div className="results-section">
          <div className="validation-status">
            <div className={`status-badge ${result.valid ? "valid" : "invalid"}`}>
              {result.valid ? "✓ Valid" : "✗ Invalid"}
            </div>
            <div className="issue-counts">
              <span className="error-count">Errors: {result.issues.filter(i => i.severity === "error").length}</span>
              <span className="warning-count">Warnings: {result.issues.filter(i => i.severity === "warning").length}</span>
              <span className="info-count">Info: {result.issues.filter(i => i.severity === "info").length}</span>
            </div>
          </div>

          <div className="filter-bar">
            <label>Filter: </label>
            <select value={filterSeverity} onChange={handleFilterChange}>
              <option value="all">All</option>
              <option value="error">Errors Only</option>
              <option value="warning">Warnings Only</option>
              <option value="info">Info Only</option>
            </select>
          </div>

          {filteredIssues.length > 0 && (
            <div className="issues-list">
              {filteredIssues.map((issue: ValidationIssue, i: number) => (
                <div key={i} className={`issue-card ${issue.severity}`}>
                  <div className="issue-header">
                    <span className="issue-severity" style={{ color: severityColor(issue.severity) }}>
                      {issue.severity.toUpperCase()}
                    </span>
                    <span className="issue-code">{issue.code}</span>
                  </div>
                  <p className="issue-message">{issue.message}</p>
                  {issue.xpath && <p className="issue-xpath">XPath: <code>{issue.xpath}</code></p>}
                  {issue.line && <p className="issue-line">Line: {issue.line}</p>}
                  {issue.fix_suggestion && (
                    <details className="fix-suggestion">
                      <summary>Fix Suggestion</summary>
                      <p>{issue.fix_suggestion}</p>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}

          {(result.passes_found.length > 0 || result.components_referenced.length > 0) && (
            <div className="metadata-section">
              {result.passes_found.length > 0 && (
                <div className="metadata-block">
                  <h4>Passes Found</h4>
                  <ul>
                    {result.passes_found.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </div>
              )}
              {result.components_referenced.length > 0 && (
                <div className="metadata-block">
                  <h4>Components Referenced</h4>
                  <ul>
                    {result.components_referenced.map((c, i) => <li key={i}><code>{c}</code></li>)}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}