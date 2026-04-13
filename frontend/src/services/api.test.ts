import { describe, it, expect, vi, beforeEach } from "vitest";
import { getAnalyses, getAnalysis } from "./api";
import type { AnalysesResponse, Analysis } from "../types";

const mockAnalysesResponse: AnalysesResponse = {
  analyses: [],
  stats: { total: 0, failed: 0, succeeded: 0, critical: 0, high_severity: 0 },
  pagination: { limit: 50, offset: 0, returned: 0 },
};

const mockAnalysis: Analysis = {
  id: "abc123",
  run_id: "run-1",
  build_id: 1,
  build_number: "1.0",
  pipeline_name: "backend-ci",
  project_name: "MyProject",
  organization: "my-org",
  result: "failed",
  summary: "Build failed.",
  root_cause: "Missing env var.",
  affected_steps: [],
  error_snippets: [],
  recommendations: [],
  severity: "high",
  confidence: 0.9,
  analyzed_at: "2024-01-01T10:00:00",
};

beforeEach(() => {
  vi.resetAllMocks();
});

describe("getAnalyses", () => {
  it("calls /api/analyses with no params by default", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockAnalysesResponse,
      })
    );

    await getAnalyses();
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("/api/analyses")
    );
  });

  it("appends filter params to the URL", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockAnalysesResponse,
      })
    );

    await getAnalyses({ project: "MyProject", result: "failed" });
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).toContain("project=MyProject");
    expect(url).toContain("result=failed");
  });

  it("omits undefined filter values from URL", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockAnalysesResponse,
      })
    );

    await getAnalyses({ project: undefined, result: "failed" });
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).not.toContain("project=");
  });

  it("throws on non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "Internal Server Error",
      })
    );

    await expect(getAnalyses()).rejects.toThrow("HTTP 500");
  });
});

describe("getAnalysis", () => {
  it("calls /api/analyses/:id", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockAnalysis,
      })
    );

    const result = await getAnalysis("abc123");
    expect(vi.mocked(fetch)).toHaveBeenCalledWith(
      expect.stringContaining("/api/analyses/abc123")
    );
    expect(result.id).toBe("abc123");
  });

  it("throws on 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        text: async () => "Not found",
      })
    );

    await expect(getAnalysis("bad-id")).rejects.toThrow("HTTP 404");
  });
});
