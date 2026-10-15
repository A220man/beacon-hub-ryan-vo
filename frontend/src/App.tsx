import { useEffect, useState } from "react";
import { RecipeAnalyzer } from "./components/RecipeAnalyzer";
import { ComponentAdvisor } from "./components/ComponentAdvisor";
import { AnswerFileValidator } from "./components/AnswerFileValidator";
import "./App.css";

interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

type Tab = "health" | "analyzer" | "advisor" | "validator";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("health");

  useEffect(() => {
    async function fetchHealth() {
      try {
        const response = await fetch("/api/v1/healthz");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        setHealth(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "health", label: "Health", icon: "🩺" },
    { id: "analyzer", label: "Recipe Analyzer", icon: "🔬" },
    { id: "advisor", label: "Component Advisor", icon: "🧠" },
    { id: "validator", label: "Answer Validator", icon: "✅" },
  ];

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Beacon Hub</h1>
          <p className="subtitle">Windows 11 Image Customization Analyzer</p>
        </div>
      </header>

      <nav className="tab-bar" role="tablist" aria-label="Main navigation">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`${tab.id}-panel`}
            id={`${tab.id}-tab`}
            className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </nav>

      <main className="main">
        {activeTab === "health" && (
          <section id="health-panel" role="tabpanel" aria-labelledby="health-tab" className="health-card card">
            <h2>System Health</h2>
            {loading && (
              <div className="loading-state">
                <span className="spinner"></span>
                <span>Checking backend connection...</span>
              </div>
            )}
            {error && (
              <div className="error-state">
                <span className="status-badge status-error">Error</span>
                <p>{error}</p>
                <button className="btn-primary" onClick={() => window.location.reload()}>
                  Retry
                </button>
              </div>
            )}
            {health && (
              <div className="health-data">
                <div className="health-row">
                  <span className="label">Status</span>
                  <span className={`status-badge ${health.status === "ok" ? "status-ok" : "status-error"}`}>
                    {health.status}
                  </span>
                </div>
                <div className="health-row">
                  <span className="label">Version</span>
                  <span className="value">{health.version}</span>
                </div>
                <div className="health-row">
                  <span className="label">Environment</span>
                  <span className="value">{health.environment}</span>
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === "analyzer" && (
          <section id="analyzer-panel" role="tabpanel" aria-labelledby="analyzer-tab">
            <RecipeAnalyzer />
          </section>
        )}

        {activeTab === "advisor" && (
          <section id="advisor-panel" role="tabpanel" aria-labelledby="advisor-tab">
            <ComponentAdvisor />
          </section>
        )}

        {activeTab === "validator" && (
          <section id="validator-panel" role="tabpanel" aria-labelledby="validator-tab">
            <AnswerFileValidator />
          </section>
        )}
      </main>

      <footer className="footer">
        <p>Beacon Hub by Ryan Vo | AI & Machine Learning</p>
      </footer>
    </div>
  );
}

export default App;