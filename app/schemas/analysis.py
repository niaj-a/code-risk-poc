from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(BaseModel):
    category: str
    severity: Severity
    title: str
    explanation: str
    file: str | None = None
    line_reference: str | None = None
    recommendation: str


class AnalysisReport(BaseModel):
    risk_level: RiskLevel
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    recommended_tests: list[str] = Field(default_factory=list)
    positive_changes: list[str] = Field(default_factory=list)
    requires_human_review: bool = True


class ManualAnalysisRequest(BaseModel):
    repository: str = Field(min_length=1)
    commit_sha: str = Field(min_length=1)
    branch: str | None = None
    diff: str = Field(min_length=1)


class AnalysisAcceptedResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus = AnalysisStatus.QUEUED


class AnalysisDetailResponse(BaseModel):
    id: str
    repository: str
    commit_sha: str
    branch: str | None
    event_type: str
    status: AnalysisStatus
    report: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


class Citation(BaseModel):
    file: str
    line_reference: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    disclaimer: str = "Advisory only — needs human review."


class HealthResponse(BaseModel):
    status: str
    environment: str
