import "@testing-library/jest-dom";
import { vi } from "vitest";

vi.mock("@testing-library/user-event", () => ({
  default: {
    setup: vi.fn(),
  },
}));

Object.defineProperty(globalThis, "fetch", {
  value: vi.fn(),
  writable: true,
  configurable: true,
});