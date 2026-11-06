
import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { RecipeAnalyzer } from "./RecipeAnalyzer";

vi.stubGlobal("fetch", vi.fn());

describe("RecipeAnalyzer", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders recipe editor with default recipe", () => {
    render(<RecipeAnalyzer />);
    expect(screen.getByText("Recipe Analyzer")).toBeInTheDocument();
    expect(screen.getByLabelText("Recipe JSON")).toBeInTheDocument();
    expect(screen.getByLabelText("Target Build")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze recipe/i })).toBeInTheDocument();
  });

  it("shows JSON error for invalid JSON", async () => {
    render(<RecipeAnalyzer defaultRecipe="invalid json" />);
    await waitFor(() => {
      expect(screen.getByText(/invalid json/i)).toBeInTheDocument();
    });
  });

  it("displays analysis result on successful API call", async () => {
    const mockResult = {
      recipe_name: "Test Recipe",
      target_build: "26100",
      analyzed_at: new Date().toISOString(),
      overall_risk: "low",
      risk_score: 0.25,
      failure_predictions: [
        {
          failure_type: "DISM_FAILURE",
          probability: 0.15,
          risk_level: "LOW",
          description: "Test description",
          evidence: ["Test evidence"],
          mitigation: "Test mitigation",
        },
      ],
      component_recommendations: [
        {
          component_name: "TestComponent",
          category: "APPS",
          recommended: true,
          risk_score: 0.1,
          reason: "Test reason",
          dependencies_satisfied: true,
          conflicts: [],
        },
      ],
      warnings: [],
      metadata: {},
    };

    (globalThis.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ analysis: mockResult }),
    });

    render(<RecipeAnalyzer />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /analyze recipe/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/overall risk: low/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/25\.0%/)).toBeInTheDocument();
    expect(screen.getByText("DISM FAILURE")).toBeInTheDocument();
    expect(screen.getByText("TestComponent")).toBeInTheDocument();
    expect(screen.getByText("Test reason")).toBeInTheDocument();
  });

  it("displays error on API failure", async () => {
    (globalThis.fetch as Mock).mockRejectedValue(new Error("API Error"));

    render(<RecipeAnalyzer />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /analyze recipe/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/api error/i)).toBeInTheDocument();
    });
  });

  it("shows loading state during analysis", async () => {
    let resolve: (value: unknown) => void;
    const promise = new Promise((r) => {
      resolve = r;
    });
    (globalThis.fetch as Mock).mockReturnValue(promise);

    render(<RecipeAnalyzer />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /analyze recipe/i }));
    });

    expect(screen.getByText(/analyzing/i)).toBeInTheDocument();

    resolve({ ok: true, json: async () => ({ analysis: { failure_predictions: [], component_recommendations: [], warnings: [], overall_risk: "low", risk_score: 0, recipe_name: "", target_build: "26100", analyzed_at: new Date().toISOString(), metadata: {} } }) });
    await promise;

    await waitFor(() => {
      expect(screen.queryByText(/analyzing/i)).not.toBeInTheDocument();
    });
  });
});
