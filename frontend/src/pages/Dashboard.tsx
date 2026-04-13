import { useState, useEffect, useCallback } from "react";
import type { Analysis, AnalysesFilters, Stats } from "../types";
import { getAnalyses } from "../services/api";
import { StatsBar } from "../components/StatsBar";
import { FilterBar } from "../components/FilterBar";
import { AnalysisRow } from "../components/AnalysisRow";

const PAGE_SIZE = 50;

const EMPTY_STATS: Stats = { total: 0, failed: 0, succeeded: 0, critical: 0, high_severity: 0 };

export function Dashboard() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [stats, setStats] = useState<Stats>(EMPTY_STATS);
  const [filters, setFilters] = useState<AnalysesFilters>({});
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (currentFilters: AnalysesFilters, currentOffset: number, append: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAnalyses(currentFilters, PAGE_SIZE, currentOffset);
        setStats(data.stats);
        setAnalyses((prev) =>
          append ? [...prev, ...data.analyses] : data.analyses
        );
        setHasMore(data.pagination.returned === PAGE_SIZE);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analyses");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    setOffset(0);
    void load(filters, 0, false);
  }, [filters, load]);

  function handleLoadMore() {
    const next = offset + PAGE_SIZE;
    setOffset(next);
    void load(filters, next, true);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Pipeline Analyses</h1>
        <p className="text-sm text-gray-500 mt-1">
          AI-generated insights from your Azure DevOps pipeline runs
        </p>
      </div>

      {/* Stats */}
      <StatsBar stats={stats} />

      {/* Filters */}
      <FilterBar filters={filters} onChange={(f) => setFilters(f)} />

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {error ? (
          <div className="p-8 text-center text-red-600 text-sm">{error}</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    {["Pipeline / Project", "Build", "Result", "Severity", "Summary", "Duration", "Analyzed"].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {analyses.length === 0 && !loading ? (
                    <tr>
                      <td colSpan={7} className="px-4 py-16 text-center text-gray-400 text-sm">
                        No analyses found. Hook up an Azure DevOps webhook to get started.
                      </td>
                    </tr>
                  ) : (
                    analyses.map((a) => <AnalysisRow key={a.id} analysis={a} />)
                  )}
                </tbody>
              </table>
            </div>

            {loading && (
              <div className="p-4 text-center">
                <span className="inline-block h-5 w-5 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
              </div>
            )}

            {hasMore && !loading && (
              <div className="p-4 text-center border-t border-gray-100">
                <button
                  onClick={handleLoadMore}
                  className="text-sm text-brand-600 hover:text-brand-700 font-medium"
                >
                  Load more
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
