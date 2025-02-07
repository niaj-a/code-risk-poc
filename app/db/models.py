import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


def utc_now() -> datetime:
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    repository: Mapped[str] = mapped_column(String(512), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(128), nullable=False)
    branch: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[AnalysisStatusEnum] = mapped_column(
        Enum(
            AnalysisStatusEnum,
            name="analysis_status",
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
        ),
