import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatsBar } from "./StatsBar";
import type { Stats } from "../types";

const makeStats = (overrides: Partial<Stats> = {}): Stats => ({
  total: 100,
  failed: 30,
  succeeded: 70,
  critical: 5,
  high_severity: 12,
  ...overrides,
});

describe("StatsBar", () => {
  it("renders total analyses count", () => {
    render(<StatsBar stats={makeStats({ total: 42 })} />);
    expect(screen.getByText("42")).toBeTruthy();
  });

  it("renders failed runs count", () => {
    render(<StatsBar stats={makeStats({ failed: 15 })} />);
    expect(screen.getByText("15")).toBeTruthy();
  });

  it("shows failure rate as percentage", () => {
    render(<StatsBar stats={makeStats({ total: 100, failed: 25 })} />);
    expect(screen.getByText("25% failure rate")).toBeTruthy();
  });

  it("shows 0% failure rate when no runs", () => {
    render(<StatsBar stats={makeStats({ total: 0, failed: 0 })} />);
    expect(screen.getByText("0% failure rate")).toBeTruthy();
  });

  it("renders critical count", () => {
    render(<StatsBar stats={makeStats({ critical: 7 })} />);
    expect(screen.getByText("7")).toBeTruthy();
  });

  it("renders all four stat cards", () => {
    render(<StatsBar stats={makeStats()} />);
    expect(screen.getByText("Total Analyses")).toBeTruthy();
    expect(screen.getByText("Failed Runs")).toBeTruthy();
    expect(screen.getByText("Critical Severity")).toBeTruthy();
    expect(screen.getByText("High Severity")).toBeTruthy();
  });
});
