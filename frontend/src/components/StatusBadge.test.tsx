import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultBadge, SeverityBadge } from "./StatusBadge";

describe("ResultBadge", () => {
  it("renders 'Failed' for failed result", () => {
    render(<ResultBadge result="failed" />);
    expect(screen.getByText("Failed")).toBeTruthy();
  });

  it("renders 'Succeeded' for succeeded result", () => {
    render(<ResultBadge result="succeeded" />);
    expect(screen.getByText("Succeeded")).toBeTruthy();
  });

  it("renders 'Partial' for partiallySucceeded result", () => {
    render(<ResultBadge result="partiallySucceeded" />);
    expect(screen.getByText("Partial")).toBeTruthy();
  });

  it("renders 'Canceled' for canceled result", () => {
    render(<ResultBadge result="canceled" />);
    expect(screen.getByText("Canceled")).toBeTruthy();
  });

  it("applies red classes for failed", () => {
    const { container } = render(<ResultBadge result="failed" />);
    expect(container.firstChild).toHaveClass("bg-red-100");
  });

  it("applies green classes for succeeded", () => {
    const { container } = render(<ResultBadge result="succeeded" />);
    expect(container.firstChild).toHaveClass("bg-green-100");
  });
});

describe("SeverityBadge", () => {
  it.each(["critical", "high", "medium", "low", "info"] as const)(
    "renders %s severity",
    (severity) => {
      render(<SeverityBadge severity={severity} />);
      expect(screen.getByText(severity)).toBeTruthy();
    }
  );

  it("applies red background for critical", () => {
    const { container } = render(<SeverityBadge severity="critical" />);
    expect(container.firstChild).toHaveClass("bg-red-600");
  });

  it("applies orange background for high", () => {
    const { container } = render(<SeverityBadge severity="high" />);
    expect(container.firstChild).toHaveClass("bg-orange-500");
  });
});
