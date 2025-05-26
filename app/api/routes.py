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
        event_type=event_type,
        status=AnalysisStatusEnum.queued,
        raw_diff=raw_diff,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    enqueue_analysis(analysis.id)
    return analysis


@router.post(
    "/api/v1/analyses/manual",
    response_model=AnalysisAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_manual_analysis(
    body: ManualAnalysisRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AnalysisAcceptedResponse:
    if not is_repository_allowed(body.repository, settings.allowed_repository_set):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Repository is not in the allowlist",
        )

    analysis = _create_and_enqueue(
        db,
        repository=body.repository,
        commit_sha=body.commit_sha,
        branch=body.branch,
        event_type="manual",
        raw_diff=body.diff,
    )
    return AnalysisAcceptedResponse(
        analysis_id=analysis.id,
        status=AnalysisStatus.QUEUED,
    )


@router.post(
    "/api/v1/webhooks/github",
    response_model=AnalysisAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def github_webhook(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
