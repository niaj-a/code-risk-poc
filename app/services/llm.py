from __future__ import annotations

import logging
from typing import Protocol

from app.core.config import Settings, get_settings
from app.schemas.analysis import (
    AnalysisReport,
    Citation,
    ChatResponse,
    Finding,
)
from app.services import mock_analyzer

logger = logging.getLogger(__name__)

DISCLAIMER = "Advisory only — needs human review."
