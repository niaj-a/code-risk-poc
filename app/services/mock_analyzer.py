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
_TLS_DISABLED = re.compile(
    r"(?i)(?:verify\s*=\s*False|VERIFY_NONE|ssl\._create_unverified_context|"
    r"CURLOPT_SSL_VERIFYPEER\s*,\s*0|rejectUnauthorized\s*:\s*false|"
    r"InsecureRequestWarning)"
)
_HARDCODED_SECRET = re.compile(
    r"(?i)(?:api[_-]?key|secret|password|token|passwd|client_secret)\s*=\s*"
    r"[\"'][^\"']{8,}[\"']"
)
_SHELL_EXEC = re.compile(
    r"(?i)(?:os\.system\s*\(|subprocess\.(?:call|run|Popen)\s*\([^)]*"
    r"shell\s*=\s*True|eval\s*\(|exec\s*\()"
)


def _line_ref_for_match(diff: str, match: re.Match[str]) -> tuple[str | None, str | None]:
    start = match.start()
