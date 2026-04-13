from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class PipelineRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    build_id: int
    build_number: str
    pipeline_name: str
    pipeline_id: int
    project_name: str
    project_id: str
    organization: str
    status: str
    result: str  # succeeded, failed, partiallySucceeded, canceled
    queue_time: Optional[str] = None
    start_time: Optional[str] = None
    finish_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    logs_url: Optional[str] = None
    build_url: Optional[str] = None
    triggered_by: Optional[str] = None
    source_branch: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    type: str = "run"


class AnalysisRecommendation(BaseModel):
    title: str
    description: str
    priority: str  # high, medium, low


class Analysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    build_id: int
    build_number: str
    pipeline_name: str
    project_name: str
    organization: str
    result: str
    source_branch: Optional[str] = None
    duration_seconds: Optional[int] = None
    summary: str
    root_cause: str
    affected_steps: List[str] = []
    error_snippets: List[str] = []
    recommendations: List[AnalysisRecommendation] = []
    severity: str  # critical, high, medium, low, info
    confidence: float = 1.0
    analyzed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    type: str = "analysis"
