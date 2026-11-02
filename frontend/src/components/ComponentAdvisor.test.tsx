
import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { ComponentAdvisor } from "./ComponentAdvisor";

vi.stubGlobal("fetch", vi.fn());

describe("ComponentAdvisor", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders build selector and categories", () => {
    render(<ComponentAdvisor />);
    expect(screen.getByText("Component Removal Advisor")).toBeInTheDocument();
    expect(screen.getByLabelText("Target Build")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /recommendations/i })).toBeInTheDocument();
  });

  it("displays component recommendations on successful API call", async () => {
    const mockRecommendations = [
      {
        component_name: "Component1",
        category: "APPS",
        recommended: true,
        reason: "Safe to remove",
        risk_score: 0.1,
        dependencies_satisfied: true,
        conflicts: [],
      },
      {
        component_name: "Component2",
        category: "SYSTEM",
        recommended: false,
        reason: "Critical system component",
        risk_score: 0.9,
        dependencies_satisfied: false,
        conflicts: [],
      },
    ];

    (globalThis.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ components: mockRecommendations }),
    });

    render(<ComponentAdvisor />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /recommendations/i }));
    });

    await waitFor(() => {
      expect(screen.getByText("Component1")).toBeInTheDocument();
      expect(screen.getByText("Component2")).toBeInTheDocument();
      expect(screen.getByText("Safe to remove")).toBeInTheDocument();
      expect(screen.getByText("Critical system component")).toBeInTheDocument();
    });
  });

  it("displays error on API failure", async () => {
    (globalThis.fetch as Mock).mockRejectedValue(new Error("API Error"));

    render(<ComponentAdvisor />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /recommendations/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/api error/i)).toBeInTheDocument();
    });
  });

  it("shows loading state during fetch", async () => {
    let resolve: (value: unknown) => void;
    const promise = new Promise((r) => {
      resolve = r;
    });
    (globalThis.fetch as Mock).mockReturnValue(promise);

    render(<ComponentAdvisor />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /recommendations/i }));
    });

    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    resolve({ ok: true, json: async () => ({ components: [] }) });
    await promise;

    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });
});
