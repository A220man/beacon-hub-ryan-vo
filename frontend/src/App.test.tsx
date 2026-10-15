import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";

vi.stubGlobal("fetch", vi.fn());

describe("App", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders header with product name", () => {
    render(<App />);
    expect(screen.getByText("Beacon Hub")).toBeInTheDocument();
    expect(screen.getByText("Windows 11 Image Customization Analyzer")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    const { promise } = Promise.withResolvers<void>();
    (globalThis.fetch as Mock).mockReturnValue(promise);
    render(<App />);
    expect(screen.getByText("Checking backend connection...")).toBeInTheDocument();
  });

  it("displays health data on successful fetch", async () => {
    (globalThis.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok", version: "1.0.0", environment: "development" }),
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("ok")).toBeInTheDocument();
    });

    expect(screen.getByText("1.0.0")).toBeInTheDocument();
    expect(screen.getByText("development")).toBeInTheDocument();
  });

  it("displays error state on fetch failure", async () => {
    (globalThis.fetch as Mock).mockRejectedValue(new Error("Network error"));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Error")).toBeInTheDocument();
    });

    expect(screen.getByText("Network error")).toBeInTheDocument();
  });

  it("shows feature list", () => {
    render(<App />);
    expect(screen.getByText("Recipe Analyzer")).toBeInTheDocument();
    expect(screen.getByText("Component Advisor")).toBeInTheDocument();
    expect(screen.getByText("Answer Validator")).toBeInTheDocument();
  });
});