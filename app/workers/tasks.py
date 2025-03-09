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

