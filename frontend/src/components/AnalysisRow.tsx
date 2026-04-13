import { useNavigate } from "react-router-dom";
import type { Analysis } from "../types";
import { ResultBadge, SeverityBadge } from "./StatusBadge";

function formatDuration(seconds?: number): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface AnalysisRowProps {
  analysis: Analysis;
}

export function AnalysisRow({ analysis }: AnalysisRowProps) {
  const navigate = useNavigate();

  return (
    <tr
      className="hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={() => navigate(`/analysis/${analysis.id}`)}
    >
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="font-medium text-gray-900 text-sm">{analysis.pipeline_name}</div>
        <div className="text-xs text-gray-500">{analysis.project_name}</div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
        #{analysis.build_number}
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <ResultBadge result={analysis.result} />
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <SeverityBadge severity={analysis.severity} />
      </td>
      <td className="px-4 py-3 text-sm text-gray-600 max-w-xs">
        <p className="truncate">{analysis.summary}</p>
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
        {formatDuration(analysis.duration_seconds)}
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-xs text-gray-400">
        {formatDate(analysis.analyzed_at)}
      </td>
    </tr>
  );
}
