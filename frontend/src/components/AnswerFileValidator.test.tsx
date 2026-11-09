
import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { AnswerFileValidator } from "./AnswerFileValidator";

vi.stubGlobal("fetch", vi.fn());

describe("AnswerFileValidator", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("renders file upload and text area", () => {
    render(<AnswerFileValidator />);
    expect(screen.getByText("Unattended Answer File Validator")).toBeInTheDocument();
    expect(screen.getByLabelText("autounattend.xml")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /validate answer file/i })).toBeInTheDocument();
  });

  it("displays validation result on successful API call", async () => {
    const mockResult = {
      valid: true,
      issues: [
        {
          severity: "INFO",
          code: "PRODUCT_KEY",
          message: "Product key found",
          xpath: "/settings/ProductKey",
          suggestion: null,
        },
      ],
      passes_found: ["specialize", "oobeSystem"],
      components_referenced: [],
    };

    (globalThis.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResult,
    });

    render(<AnswerFileValidator />);
    fireEvent.change(screen.getByLabelText("autounattend.xml"), {
      target: { value: "<unattend></unattend>" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /validate answer file/i }));
    });

    await waitFor(() => {
      expect(screen.getByText("✓ Valid")).toBeInTheDocument();
    });
    expect(screen.getByText("PRODUCT_KEY")).toBeInTheDocument();
    expect(screen.getByText("specialize")).toBeInTheDocument();
  });

  it("displays validation errors on API failure", async () => {
    const mockResult = {
      valid: false,
      issues: [
        {
          severity: "ERROR",
          code: "PRODUCT_KEY",
          message: "Product key is missing",
          xpath: "/settings/ProductKey",
          suggestion: "Add a product key",
        },
      ],
      passes_found: [],
      components_referenced: [],
    };

    (globalThis.fetch as Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResult,
    });

    render(<AnswerFileValidator />);
    fireEvent.change(screen.getByLabelText("autounattend.xml"), {
      target: { value: "<unattend></unattend>" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /validate answer file/i }));
    });

    await waitFor(() => {
      expect(screen.getByText("✗ Invalid")).toBeInTheDocument();
    });
    expect(screen.getByText("Product key is missing")).toBeInTheDocument();
    expect(screen.getByText("ERROR")).toBeInTheDocument();
  });

  it("displays error on API failure", async () => {
    (globalThis.fetch as Mock).mockRejectedValue(new Error("API Error"));

    render(<AnswerFileValidator />);
    fireEvent.change(screen.getByLabelText("autounattend.xml"), {
      target: { value: "<unattend></unattend>" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /validate answer file/i }));
    });

    await waitFor(() => {
      expect(screen.getByText(/api error/i)).toBeInTheDocument();
    });
  });

  it("shows loading state during validation", async () => {
    const { promise, resolve } = Promise.withResolvers<unknown>();
    (globalThis.fetch as Mock).mockReturnValue(promise);

    render(<AnswerFileValidator />);
    fireEvent.change(screen.getByLabelText("autounattend.xml"), {
      target: { value: "<unattend></unattend>" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /validate answer file/i }));
    });

    expect(screen.getByText(/validating/i)).toBeInTheDocument();

    resolve({ ok: true, json: async () => ({ valid: true, issues: [], passes_found: [], components_referenced: [] }) });
    await promise;

    await waitFor(() => {
      expect(screen.queryByText(/validating/i)).not.toBeInTheDocument();
    });
  });
});
