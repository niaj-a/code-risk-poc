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
    try:
        limited = analysis.raw_diff[: settings.max_diff_chars]
        redacted = redact_sensitive_content(limited)
        analysis.redacted_diff = redacted
        db.commit()

        analyzer = get_analyzer(settings)
        report = analyzer.analyze(redacted)
        report.requires_human_review = True

        analysis.report = report.model_dump(mode="json")
        analysis.status = AnalysisStatusEnum.completed
        analysis.error_message = None
        _touch(analysis)
        db.commit()
        logger.info("analysis done: %s", analysis_id)
    except Exception:
        logger.exception("analysis failed id=%s", analysis_id)
        db.rollback()
        analysis = db.get(Analysis, analysis_id)
        if analysis is not None:
            analysis.status = AnalysisStatusEnum.failed
            analysis.error_message = SAFE_FAILURE_MESSAGE
            _touch(analysis)
            db.commit()
        raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_analysis",
    max_retries=3,
