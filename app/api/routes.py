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
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
) -> AnalysisAcceptedResponse:
    raw_body = await request.body()

    if not verify_github_signature(
        raw_body, x_hub_signature_256, settings.github_webhook_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook signature",
        )

    if not x_github_event or x_github_event not in SUPPORTED_GITHUB_EVENTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported GitHub event: {x_github_event}",
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc

    try:
        parsed = parse_github_event(x_github_event, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if not is_repository_allowed(parsed.repository, settings.allowed_repository_set):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Repository is not in the allowlist",
        )

    logger.info("github %s from %s", parsed.event_type, parsed.repository)

    analysis = _create_and_enqueue(
        db,
        repository=parsed.repository,
        commit_sha=parsed.commit_sha,
        branch=parsed.branch,
        event_type=parsed.event_type,
        raw_diff=parsed.raw_diff,
    )
