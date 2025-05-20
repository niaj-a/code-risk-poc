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
