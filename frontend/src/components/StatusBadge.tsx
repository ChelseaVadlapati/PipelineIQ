import clsx from "clsx";
import type { PipelineResult, Severity } from "../types";

const RESULT_STYLES: Record<PipelineResult, string> = {
  failed: "bg-red-100 text-red-700 border-red-200",
  succeeded: "bg-green-100 text-green-700 border-green-200",
  partiallySucceeded: "bg-yellow-100 text-yellow-700 border-yellow-200",
  canceled: "bg-gray-100 text-gray-600 border-gray-200",
};

const RESULT_LABELS: Record<PipelineResult, string> = {
  failed: "Failed",
  succeeded: "Succeeded",
  partiallySucceeded: "Partial",
  canceled: "Canceled",
};

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-500 text-white",
  medium: "bg-yellow-400 text-yellow-900",
  low: "bg-blue-100 text-blue-700",
  info: "bg-gray-100 text-gray-600",
};

interface ResultBadgeProps {
  result: PipelineResult;
  className?: string;
}

export function ResultBadge({ result, className }: ResultBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
        RESULT_STYLES[result] ?? "bg-gray-100 text-gray-600 border-gray-200",
        className
      )}
    >
      {RESULT_LABELS[result] ?? result}
    </span>
  );
}

interface SeverityBadgeProps {
  severity: Severity;
  className?: string;
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide",
        SEVERITY_STYLES[severity] ?? "bg-gray-100 text-gray-600",
        className
      )}
    >
      {severity}
    </span>
  );
}
