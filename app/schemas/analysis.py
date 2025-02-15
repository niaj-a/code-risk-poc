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
