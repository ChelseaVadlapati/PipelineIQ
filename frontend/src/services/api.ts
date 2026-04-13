import type { Analysis, AnalysesResponse, AnalysesFilters } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== ""
  );
  if (!entries.length) return "";
  return "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join("&");
}

export async function getAnalyses(
  filters: AnalysesFilters = {},
  limit = 50,
  offset = 0
): Promise<AnalysesResponse> {
  const query = buildQuery({
    limit,
    offset,
    project: filters.project,
    pipeline: filters.pipeline,
    result: filters.result,
    severity: filters.severity,
  });
  return fetchJSON<AnalysesResponse>(`${BASE_URL}/analyses${query}`);
}

export async function getAnalysis(id: string): Promise<Analysis> {
  return fetchJSON<Analysis>(`${BASE_URL}/analyses/${id}`);
}
