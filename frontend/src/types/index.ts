export type PipelineResult =
  | "succeeded"
  | "failed"
  | "partiallySucceeded"
  | "canceled";

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export type RecommendationPriority = "high" | "medium" | "low";

export interface Recommendation {
  title: string;
  description: string;
  priority: RecommendationPriority;
}

export interface Analysis {
  id: string;
  run_id: string;
  build_id: number;
  build_number: string;
  pipeline_name: string;
  project_name: string;
  organization: string;
  result: PipelineResult;
  source_branch?: string;
  duration_seconds?: number;
  summary: string;
  root_cause: string;
  affected_steps: string[];
  error_snippets: string[];
  recommendations: Recommendation[];
  severity: Severity;
  confidence: number;
  analyzed_at: string;
}

export interface Stats {
  total: number;
  failed: number;
  succeeded: number;
  critical: number;
  high_severity: number;
}

export interface AnalysesResponse {
  analyses: Analysis[];
  stats: Stats;
  pagination: {
    limit: number;
    offset: number;
    returned: number;
  };
}

export interface AnalysesFilters {
  project?: string;
  pipeline?: string;
  result?: PipelineResult;
  severity?: Severity;
}
