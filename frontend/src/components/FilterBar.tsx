import type { AnalysesFilters, PipelineResult, Severity } from "../types";

interface FilterBarProps {
  filters: AnalysesFilters;
  onChange: (f: AnalysesFilters) => void;
}

const RESULTS: { value: PipelineResult | ""; label: string }[] = [
  { value: "", label: "All results" },
  { value: "failed", label: "Failed" },
  { value: "partiallySucceeded", label: "Partial" },
  { value: "canceled", label: "Canceled" },
];

const SEVERITIES: { value: Severity | ""; label: string }[] = [
  { value: "", label: "All severities" },
  { value: "critical", label: "Critical" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

export function FilterBar({ filters, onChange }: FilterBarProps) {
  return (
    <div className="flex flex-wrap gap-3 items-center">
      <input
        type="text"
        placeholder="Filter by project…"
        value={filters.project ?? ""}
        onChange={(e) => onChange({ ...filters, project: e.target.value || undefined })}
        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
      <input
        type="text"
        placeholder="Filter by pipeline…"
        value={filters.pipeline ?? ""}
        onChange={(e) => onChange({ ...filters, pipeline: e.target.value || undefined })}
        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
      <select
        value={filters.result ?? ""}
        onChange={(e) =>
          onChange({ ...filters, result: (e.target.value as PipelineResult) || undefined })
        }
        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
      >
        {RESULTS.map((r) => (
          <option key={r.value} value={r.value}>
            {r.label}
          </option>
        ))}
      </select>
      <select
        value={filters.severity ?? ""}
        onChange={(e) =>
          onChange({ ...filters, severity: (e.target.value as Severity) || undefined })
        }
        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
      >
        {SEVERITIES.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>

      {(filters.project || filters.pipeline || filters.result || filters.severity) && (
        <button
          onClick={() => onChange({})}
          className="text-xs text-gray-500 hover:text-gray-700 underline"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
