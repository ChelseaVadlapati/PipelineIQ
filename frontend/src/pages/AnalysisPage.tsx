import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { Analysis } from "../types";
import { getAnalysis } from "../services/api";
import { ResultBadge, SeverityBadge } from "../components/StatusBadge";

function formatDuration(seconds?: number): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
    </div>
  );
}

const PRIORITY_COLOR: Record<string, string> = {
  high: "border-l-red-500",
  medium: "border-l-yellow-400",
  low: "border-l-blue-400",
};

export function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getAnalysis(id)
      .then(setAnalysis)
      .catch((err) => setError(err instanceof Error ? err.message : "Not found"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="inline-block h-8 w-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <p className="text-red-600 font-medium">{error ?? "Analysis not found"}</p>
        <Link to="/" className="mt-4 inline-block text-sm text-brand-600 hover:underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Back link */}
      <Link to="/" className="inline-flex items-center text-sm text-brand-600 hover:underline gap-1">
        <span>&#8592;</span> All analyses
      </Link>

      {/* Header card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{analysis.pipeline_name}</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {analysis.project_name} &middot; Build #{analysis.build_number}
              {analysis.source_branch && (
                <span className="ml-2 font-mono text-xs bg-gray-100 px-1.5 py-0.5 rounded">
                  {analysis.source_branch.replace("refs/heads/", "")}
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <ResultBadge result={analysis.result} />
            <SeverityBadge severity={analysis.severity} />
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Duration</p>
            <p className="font-medium text-gray-900">{formatDuration(analysis.duration_seconds)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Analyzed</p>
            <p className="font-medium text-gray-900">{formatDate(analysis.analyzed_at)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">
              AI Confidence
            </p>
            <ConfidenceBar value={analysis.confidence} />
          </div>
        </div>
      </div>

      {/* Summary & Root cause */}
      <div className="grid sm:grid-cols-2 gap-4">
        <Section title="Summary">
          <p className="text-sm text-gray-700 leading-relaxed">{analysis.summary}</p>
        </Section>
        <Section title="Root Cause">
          <p className="text-sm text-gray-700 leading-relaxed">{analysis.root_cause}</p>
        </Section>
      </div>

      {/* Affected steps */}
      {analysis.affected_steps.length > 0 && (
        <Section title="Affected Steps">
          <ul className="flex flex-wrap gap-2">
            {analysis.affected_steps.map((step) => (
              <li
                key={step}
                className="text-xs font-mono bg-red-50 text-red-700 border border-red-100 rounded px-2 py-1"
              >
                {step}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Error snippets */}
      {analysis.error_snippets.length > 0 && (
        <Section title="Key Error Messages">
          <div className="space-y-2">
            {analysis.error_snippets.map((snippet, i) => (
              <pre
                key={i}
                className="text-xs font-mono bg-gray-900 text-red-300 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap"
              >
                {snippet}
              </pre>
            ))}
          </div>
        </Section>
      )}

      {/* Recommendations */}
      {analysis.recommendations.length > 0 && (
        <Section title="Recommendations">
          <div className="space-y-3">
            {analysis.recommendations.map((rec, i) => (
              <div
                key={i}
                className={`border-l-4 bg-white border border-gray-200 rounded-r-lg p-4 ${
                  PRIORITY_COLOR[rec.priority] ?? "border-l-gray-300"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <p className="text-sm font-semibold text-gray-900">{rec.title}</p>
                  <span className="text-xs text-gray-400 uppercase">{rec.priority}</span>
                </div>
                <p className="text-sm text-gray-600 leading-relaxed">{rec.description}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
      <h2 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">{title}</h2>
      {children}
    </div>
  );
}
