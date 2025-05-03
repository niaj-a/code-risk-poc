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
    preceding = diff[:start]
    file_name: str | None = None
    for line in reversed(preceding.splitlines()):
        if line.startswith("+++ b/") or line.startswith("+++ "):
            file_name = line.replace("+++ b/", "").replace("+++ ", "").strip()
            if file_name != "/dev/null":
                break
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 4:
                file_name = parts[3].removeprefix("b/")
            break

    hunk_matches = list(re.finditer(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", preceding))
    if hunk_matches:
        last = hunk_matches[-1]
        start_line = int(last.group(1))
        segment = preceding[last.end() :]
        added = sum(
            1 for ln in segment.splitlines() if ln.startswith("+") and not ln.startswith("+++")
        )
        return file_name, str(start_line + added)
    return file_name, None


def analyze_diff(diff: str) -> AnalysisReport:
    findings: list[Finding] = []

    for pattern, builder in (
        (
            _SQL_FSTRING,
            lambda f, lr: Finding(
                category="sql_injection",
                severity=Severity.HIGH,
                title="Possible SQL injection via interpolated query",
                explanation=(
                    "Looks like SQL built with an f-string. If user input lands here, "
                    "that's classic injection territory."
                ),
                file=f,
                line_reference=lr,
                recommendation="Use parameterized queries / bound params.",
            ),
        ),
        (
            _SQL_FORMAT,
            lambda f, lr: Finding(
                category="sql_injection",
                severity=Severity.HIGH,
                title="Possible SQL injection via string formatting",
                explanation=(
                    "SQL-ish text with % formatting or concatenation. Check whether "
                    "inputs are trusted and whether params are used."
                ),
                file=f,
                line_reference=lr,
                recommendation="Switch to parameterized statements.",
            ),
        ),
        (
            _SENSITIVE_LOG,
            lambda f, lr: Finding(
                category="sensitive_data_logging",
                severity=Severity.HIGH,
                title="Possible sensitive data in logs",
                explanation=(
                    "Log/print path mentions customer, account, card, password, or token. "
                    "Easy way to leak PII into log stores."
                ),
                file=f,
                line_reference=lr,
