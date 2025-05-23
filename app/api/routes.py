from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import is_repository_allowed, verify_github_signature
from app.db.models import Analysis, AnalysisStatusEnum
from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisAcceptedResponse,
    AnalysisDetailResponse,
    AnalysisReport,
    AnalysisStatus,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ManualAnalysisRequest,
)
from app.services.github import parse_github_event
from app.services.llm import DISCLAIMER, get_chat_responder
from app.workers.tasks import enqueue_analysis

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_GITHUB_EVENTS = frozenset({"push", "pull_request"})


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)


def _create_and_enqueue(
    db: Session,
    *,
    repository: str,
    commit_sha: str,
    branch: str | None,
    event_type: str,
    raw_diff: str,
) -> Analysis:
    analysis = Analysis(
        repository=repository,
        commit_sha=commit_sha,
        branch=branch,
