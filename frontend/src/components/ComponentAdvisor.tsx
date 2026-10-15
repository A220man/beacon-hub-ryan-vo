import { useState, useEffect } from "react";
import { getComponentRecommendations, getComponentDatabase, ComponentRecommendation, ComponentInfo } from "../api/client";
import "./ComponentAdvisor.css";

export function ComponentAdvisor() {
  const [targetBuild, setTargetBuild] = useState("26100");
  const [category, setCategory] = useState<string>("all");
  const [includeUnsafe, setIncludeUnsafe] = useState(false);
  const [recommendations, setRecommendations] = useState<ComponentRecommendation[]>([]);
  const [database, setDatabase] = useState<ComponentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"recommendations" | "database">("recommendations");

  const categories = ["all", "apps", "capabilities", "drivers", "features", "languages", "services", "system"];

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const cats = category === "all" ? undefined : [category];
      const recs = await getComponentRecommendations(targetBuild, cats, includeUnsafe);
      setRecommendations(recs);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load recommendations");
    } finally {
      setLoading(false);
    }
  };

  const fetchDatabase = async () => {
    setLoading(true);
    setError(null);
    try {
      const db = await getComponentDatabase(targetBuild);
      setDatabase(db.components);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load database");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (view === "recommendations") {
      fetchRecommendations();
    } else {
      fetchDatabase();
    }
  }, [targetBuild, category, includeUnsafe, view]);

  const riskColor = (score: number) => {
    if (score >= 0.7) return "var(--color-error)";
    if (score >= 0.5) return "var(--color-warning)";
    return "var(--color-success)";
  };

  return (
    <div className="component-advisor card">
      <div className="header">
        <h2>Component Removal Advisor</h2>
        <p className="description">Get AI-powered recommendations for safe component removals per Windows build version.</p>
      </div>

      <div className="controls">
        <div className="control-group">
          <label htmlFor="advisor-build">Target Build</label>
          <select id="advisor-build" value={targetBuild} onChange={(e) => setTargetBuild(e.target.value)}>
            <option value="22000">22H2 (22000)</option>
            <option value="22621">23H2 (22621)</option>
            <option value="25398">24H2 (25398)</option>
            <option value="26100">26H2 (26100)</option>
            <option value="26300">Insider 26300+</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="advisor-category">Category</label>
          <select id="advisor-category" value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === "all" ? "All Categories" : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={includeUnsafe}
              onChange={(e) => setIncludeUnsafe(e.target.checked)}
            />
            Include unsafe/core components
          </label>
        </div>

        <div className="view-toggle">
          <button
            className={view === "recommendations" ? "active" : ""}
            onClick={() => setView("recommendations")}
          >
            Recommendations
          </button>
          <button
            className={view === "database" ? "active" : ""}
            onClick={() => setView("database")}
          >
            Full Database
          </button>
        </div>
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {loading ? (
        <div className="loading-state">
          <span className="spinner"></span>
          <span>Loading {view === "recommendations" ? "recommendations" : "database"}...</span>
        </div>
      ) : view === "recommendations" ? (
        <div className="recommendations-view">
          <div className="summary">
            <span>{recommendations.length} components</span>
            <span className="recommended-count">
              {recommendations.filter(r => r.recommended).length} recommended
            </span>
          </div>
          <table>
            <thead>
              <tr>
                <th>Component</th>
                <th>Category</th>
                <th>Recommended</th>
                <th>Risk Score</th>
                <th>Dependencies</th>
                <th>Conflicts</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {recommendations.map((rec, i) => (
                <tr key={i} className={rec.recommended ? "recommended" : "not-recommended"}>
                  <td><code>{rec.component_name}</code></td>
                  <td>{rec.category}</td>
                  <td>{rec.recommended ? "✓ Yes" : "✗ No"}</td>
                  <td>
                    <span className="risk-badge" style={{ backgroundColor: `${riskColor(rec.risk_score)}20`, color: riskColor(rec.risk_score) }}>
                      {(rec.risk_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>{rec.dependencies_satisfied ? "✓ Satisfied" : "✗ Missing"}</td>
                  <td>{rec.conflicts.length > 0 ? rec.conflicts.join(", ") : "None"}</td>
                  <td>{rec.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="database-view">
          <div className="summary">{database.length} components available for build {targetBuild}</div>
          <table>
            <thead>
              <tr>
                <th>Component</th>
                <th>Category</th>
                <th>Size (MB)</th>
                <th>Safe to Remove</th>
                <th>Dependencies</th>
                <th>Conflicts</th>
                <th>Build Range</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {database.map((comp, i) => (
                <tr key={i}>
                  <td><code>{comp.name}</code></td>
                  <td>{comp.category}</td>
                  <td>{comp.size_mb}</td>
                  <td>{comp.safe_to_remove ? "✓ Yes" : "✗ No"}</td>
                  <td>{comp.dependencies.join(", ") || "None"}</td>
                  <td>{comp.conflicts.join(", ") || "None"}</td>
                  <td>{comp.min_build} – {comp.max_build}</td>
                  <td>{comp.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}