from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import session as db_session
from app.db.models import Analysis, AnalysisStatusEnum
from app.services.llm import get_analyzer
from app.services.redaction import redact_sensitive_content
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

SAFE_FAILURE_MESSAGE = (
    "Analysis failed due to an internal error. Retry later or ping the platform team."
)


def _touch(analysis: Analysis) -> None:
    analysis.updated_at = datetime.now(timezone.utc)


def run_analysis_pipeline(db: Session, analysis_id: str) -> None:
    settings = get_settings()
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        logger.error("analysis missing: %s", analysis_id)
        return

    analysis.status = AnalysisStatusEnum.running
    analysis.error_message = None
