"""Heuristic analyzer for local runs without an LLM key."""

from __future__ import annotations

import re

from app.schemas.analysis import AnalysisReport, Finding, RiskLevel, Severity

_SQL_FSTRING = re.compile(
    r"(?i)f[\"'][^\"']*(?:SELECT|INSERT|UPDATE|DELETE|DROP)\b[^\"']*\{[^}]+\}[^\"']*[\"']"
)
_SQL_FORMAT = re.compile(
    r"(?i)(?:SELECT|INSERT|UPDATE|DELETE|DROP)\b[^\"'\n]*(?:%s|\.format\(|\+)"
)
_SENSITIVE_LOG = re.compile(
    r"(?i)(?:log|logger|logging|print|console\.(?:log|info|debug|warn|error))"
    r"[^\n]*(?:customer|account|card|password|token)"
)
