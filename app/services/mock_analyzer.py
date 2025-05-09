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
                recommendation="Drop or redact sensitive fields before logging.",
            ),
        ),
        (
            _TLS_DISABLED,
            lambda f, lr: Finding(
                category="tls_verification",
                severity=Severity.CRITICAL,
                title="TLS certificate verification appears disabled",
                explanation=(
                    "verify=False / similar. Opens the door to MITM on outbound calls."
                ),
                file=f,
                line_reference=lr,
                recommendation="Keep cert verification on; fix the trust store instead.",
            ),
        ),
        (
            _HARDCODED_SECRET,
            lambda f, lr: Finding(
                category="secrets",
                severity=Severity.CRITICAL,
                title="Possible hardcoded secret",
                explanation=(
                    "Looks like an api key / password / token baked into source. "
                    "Rotate it and pull from a secret store."
                ),
                file=f,
                line_reference=lr,
                recommendation="Remove from code, rotate, load from vault/env at runtime.",
            ),
        ),
        (
            _SHELL_EXEC,
            lambda f, lr: Finding(
                category="command_injection",
                severity=Severity.HIGH,
                title="Dangerous shell or dynamic execution",
                explanation=(
                    "os.system / shell=True / eval / exec. Bad news if args include "
                    "untrusted input."
                ),
                file=f,
                line_reference=lr,
                recommendation="Prefer argv lists; avoid shell=True and eval/exec.",
            ),
        ),
    ):
        for match in pattern.finditer(diff):
            file_name, line_ref = _line_ref_for_match(diff, match)
            finding = builder(file_name, line_ref)
            key = (finding.title, finding.file, finding.line_reference)
            if any(
                (existing.title, existing.file, existing.line_reference) == key
                for existing in findings
            ):
                continue
            findings.append(finding)

    if "METADATA ONLY" in diff.upper() or "not a complete code diff" in diff.lower():
        findings.append(
            Finding(
                category="incomplete_context",
                severity=Severity.MEDIUM,
                title="Analysis based on metadata only",
                explanation=(
                    "No full patch in the payload — we're working off event metadata. "
                    "Don't treat this as a real diff review."
                ),
                file=None,
                line_reference=None,
                recommendation="Wire up a GitHub App (or similar) to fetch the real diff.",
            )
        )

    risk = _aggregate_risk(findings)
    recommended_tests = [
        "Authn/authz tests if those paths changed",
        "Injection coverage on touched data-access code",
        "Regression on payment/account flows if relevant",
    ]
    positive: list[str] = []
    if not findings:
        positive.append("No heuristic hits — still not a free pass.")

    summary = (
        f"Mock analyzer found {len(findings)} issue(s), "
        f"risk_level={risk.value}. Human review still required."
