import type { Stats } from "../types";

interface StatCardProps {
  label: string;
  value: number | string;
  sub?: string;
  accent?: string;
}

function StatCard({ label, value, sub, accent = "text-gray-900" }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-3xl font-bold ${accent}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  );
}

interface StatsBarProps {
  stats: Stats;
}

export function StatsBar({ stats }: StatsBarProps) {
  const failureRate =
    stats.total > 0 ? Math.round((stats.failed / stats.total) * 100) : 0;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <StatCard label="Total Analyses" value={stats.total} />
      <StatCard
        label="Failed Runs"
        value={stats.failed}
        sub={`${failureRate}% failure rate`}
        accent={stats.failed > 0 ? "text-red-600" : "text-gray-900"}
      />
      <StatCard
        label="Critical Severity"
        value={stats.critical}
        accent={stats.critical > 0 ? "text-red-600" : "text-gray-900"}
      />
      <StatCard
        label="High Severity"
        value={stats.high_severity}
        accent={stats.high_severity > 0 ? "text-orange-500" : "text-gray-900"}
      />
    </div>
  );
}
