import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth, useAuthCallback } from "./auth";
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
  const navigate = useNavigate();
  const { user, isAuthenticated, login, logout, loading } = useAuth();
  const authReady = useAuthCallback();

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "health", label: "Health", icon: "🩺" },
    { id: "analyzer", label: "Recipe Analyzer", icon: "🔬" },
    { id: "advisor", label: "Component Advisor", icon: "🧠" },
    { id: "validator", label: "Answer Validator", icon: "✅" },
  ];

  // Wait for auth to resolve before rendering tabs
  if (loading || !authReady) {
    return (
      <div className="app">
        <header className="header">
          <div className="header-content">
            <h1>Beacon Hub</h1>
            <p className="subtitle">Windows 11 Image Customization Analyzer</p>
          </div>
        </header>
        <main className="main">
          <div className="loading-state">
            <span className="spinner"></span>
            <span>Initializing authentication...</span>
          </div>
        </main>
      </div>
    );
  }

  // If not authenticated, show login option
  if (!isAuthenticated) {
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
              aria-selected={false}
              aria-controls={`${tab.id}-panel`}
              id={`${tab.id}-tab`}
              className={`tab-button disabled`}
              onClick={() => {}}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </nav>
        <main className="main">
          <div className="auth-card card">
            <h2>Authentication Required</h2>
            <p>
              Sign in with Keycloak to access protected features.
            </p>
            <button
              className="btn-primary"
              onClick={() => {
                login();
              }}
            >
              Login with Keycloak
            </button>
          </div>
        </main>
        <footer className="footer">
          <p>Beacon Hub by Ryan Vo | AI & Machine Learning</p>
        </footer>
      </div>
    );
  }

  // If authenticated, show normal UI
  useEffect(() => {
    // Fetch health data when user becomes authenticated
    const fetchHealth = async () => {
      try {
        const response = await fetch("/api/v1/healthz");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        // Health is now available but not rendered in tab bar UI
      } catch (err) {
        console.error("Health check failed:", err);
      }
    };
    fetchHealth();
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <h1>Beacon Hub</h1>
          <p className="subtitle">Windows 11 Image Customization Analyzer</p>
        </div>
        <div className="header-right">
          <button
            className="btn-secondary"
            onClick={() => {
              logout();
            }}
          >
            Logout
          </button>
        </div>
      </header>

      <nav className="tab-bar" role="tablist" aria-label="Main navigation">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={false}
            aria-controls={`${tab.id}-panel`}
            id={`${tab.id}-tab`}
            className={`tab-button ${false ? "active" : ""}`}
            onClick={() => {}}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        ))}
      </nav>

      <main className="main">
        {isAuthenticated && (
          <section id="health-panel" role="tabpanel" aria-labelledby="health-tab" className="health-card card">
            <h2>System Health</h2>
            <p>Welcome, {user?.username || "user"}</p>
          </section>
        )}

        {isAuthenticated && (
          {activeTab === "analyzer" && (
            <section id="analyzer-panel" role="tabpanel" aria-labelledby="analyzer-tab">
              <RecipeAnalyzer />
            </section>
          )}}

        {isAuthenticated && (
          {activeTab === "advisor" && (
            <section id="advisor-panel" role="tabpanel" aria-labelledby="advisor-tab">
              <ComponentAdvisor />
            </section>
          )}}

        {isAuthenticated && (
          {activeTab === "validator" && (
            <section id="validator-panel" role="tabpanel" aria-labelledby="validator-tab">
              <AnswerFileValidator />
            </section>
          )}}
        )}
      </main>

      <footer className="footer">
        <p>Beacon Hub by Ryan Vo | AI & Machine Learning</p>
      </footer>
    </div>
  );
}

export default App;
