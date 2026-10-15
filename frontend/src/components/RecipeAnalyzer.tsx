import { useState } from "react";
import { analyzeRecipe, AnalysisResult, FailurePrediction, ComponentRecommendation } from "../api/client";
import "./RecipeAnalyzer.css";

interface RecipeAnalyzerProps {
  defaultRecipe?: string;
  defaultBuild?: string;
}

export function RecipeAnalyzer({ defaultRecipe, defaultBuild = "26100" }: RecipeAnalyzerProps) {
  const [recipeJson, setRecipeJson] = useState(defaultRecipe || JSON.stringify({
    name: "Example Recipe",
    description: "Windows 11 24H2 Pro - Minimal",
    target_build: "26100",
    components: [
      { name: "Microsoft.Edge", category: "apps", safe_to_remove: true, size_mb: 180 },
      { name: "Microsoft.Store", category: "apps", safe_to_remove: true, size_mb: 45 },
      { name: "DiagTrack", category: "services", safe_to_remove: true, size_mb: 5 },
      { name: "ReservedStorage", category: "system", safe_to_remove: true, size_mb: 7000 },
    ],
  }, null, 2));
  const [targetBuild, setTargetBuild] = useState(defaultBuild);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    let recipe: Record<string, unknown>;
    try {
      recipe = JSON.parse(recipeJson);
      setJsonError(null);
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : "Invalid JSON");
      setLoading(false);
      return;
    }

    try {
      const analysis = await analyzeRecipe(recipe, targetBuild);
      setResult(analysis);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const riskColor = (level: string) => {
    switch (level) {
      case "critical": return "var(--color-error)";
      case "high": return "var(--color-error)";
      case "medium": return "var(--color-warning)";
      case "low": return "var(--color-success)";
      default: return "var(--color-text-muted)";
    }
  };

  return (
    <div className="recipe-analyzer card">
      <h2>Recipe Analyzer</h2>
      <p className="description">Analyze Windows 11 component removal recipes for DISM failure risk, registry issues, and ADK compatibility.</p>

      <div className="input-section">
        <div className="input-group">
          <label htmlFor="target-build">Target Build</label>
          <select id="target-build" value={targetBuild} onChange={(e) => setTargetBuild(e.target.value)}>
            <option value="22000">22H2 (22000)</option>
            <option value="22621">23H2 (22621)</option>
            <option value="25398">24H2 (25398)</option>
            <option value="26100">26H2 (26100)</option>
            <option value="26300">Insider 26300+</option>
          </select>
        </div>

        <div className="input-group full-width">
          <label htmlFor="recipe-json">Recipe JSON</label>
          <textarea
            id="recipe-json"
            value={recipeJson}
            onChange={(e) => setRecipeJson(e.target.value)}
            rows={12}
            spellCheck={false}
            className={jsonError ? "error" : ""}
            placeholder='{"name": "My Recipe", "description": "...", "target_build": "26100", "components": [...]}'
          />
          {jsonError && <span className="error-msg">{jsonError}</span>}
        </div>

        <button className="btn-primary" onClick={handleAnalyze} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Recipe"}
        </button>
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {result && (
        <div className="results-section">
          <div className="risk-summary">
            <div className="risk-badge" style={{ backgroundColor: `${riskColor(result.overall_risk)}20`, color: riskColor(result.overall_risk) }}>
              Overall Risk: {result.overall_risk.toUpperCase()}
            </div>
            <div className="risk-score">Risk Score: {(result.risk_score * 100).toFixed(1)}%</div>
          </div>

          <div className="predictions">
            <h3>Failure Predictions</h3>
            {result.failure_predictions.map((pred: FailurePrediction, i: number) => (
              <div key={i} className={`prediction-card ${pred.risk_level}`}>
                <div className="prediction-header">
                  <span className="prediction-type">{pred.failure_type.replace(/_/g, " ")}</span>
                  <span className={`prediction-prob ${pred.risk_level}`}>{(pred.probability * 100).toFixed(1)}%</span>
                </div>
                <p className="prediction-desc">{pred.description}</p>
                <details>
                  <summary>Evidence</summary>
                  <ul>
                    {pred.evidence.map((e, idx) => <li key={idx}>{e}</li>)}
                  </ul>
                </details>
                {pred.mitigation && (
                  <details>
                    <summary>Mitigation</summary>
                    <p>{pred.mitigation}</p>
                  </details>
                )}
              </div>
            ))}
          </div>

          <div className="recommendations">
            <h3>Component Recommendations</h3>
            <table>
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Category</th>
                  <th>Recommended</th>
                  <th>Risk</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {result.component_recommendations.map((rec: ComponentRecommendation, i: number) => (
                  <tr key={i} className={rec.recommended ? "recommended" : "not-recommended"}>
                    <td>{rec.component_name}</td>
                    <td>{rec.category}</td>
                    <td>{rec.recommended ? "✓ Yes" : "✗ No"}</td>
                    <td><span className={`risk-score ${rec.risk_score > 0.5 ? "high" : "low"}`}>{(rec.risk_score * 100).toFixed(0)}%</span></td>
                    <td>{rec.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {result.warnings.length > 0 && (
            <div className="warnings">
              <h3>Warnings</h3>
              <ul>
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}