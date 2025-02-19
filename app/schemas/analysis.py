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
