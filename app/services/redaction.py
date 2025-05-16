"""Best-effort secret scrubbing before anything hits an LLM. Not real DLP."""

from __future__ import annotations

import re

REDACTION_PLACEHOLDER = "[REDACTED]"

_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"-----BEGIN(?:\s+\w+)?\s+PRIVATE KEY-----[\s\S]*?"
        r"-----END(?:\s+\w+)?\s+PRIVATE KEY-----",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?i)(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp|mssql)"
        r"://[^\s\"']+",
    ),
    re.compile(
        r"(?i)(?:Server|Data Source)=[^;\s]+;.*?(?:Password|Pwd)=[^;\s]+",
    ),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)(Authorization:\s*)\S+"),
    re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"(?i)((?:api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|"
        r"client[_-]?secret|auth[_-]?token|private[_-]?key|password|passwd|pwd|"
        r"secret|token)\s*[=:]\s*)([\"']?)[^\s\"'#]+(\2)"
    ),
    # rough PAN scrub; no Luhn check
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
]


def redact_sensitive_content(text: str) -> str:
    result = text
    for pattern in _PATTERNS:
        if pattern.groups:

            def _repl(match: re.Match[str], _p: re.Pattern[str] = pattern) -> str:
                if _p.groups >= 1 and match.lastindex and match.lastindex >= 1:
                    prefix = match.group(1)
                    if prefix.lower().startswith("bearer") or prefix.lower().startswith(
                        "authorization"
                    ):
                        return f"{prefix}{REDACTION_PLACEHOLDER}"
                    if _p.groups >= 3:
                        quote = match.group(2) or ""
                        return f"{prefix}{quote}{REDACTION_PLACEHOLDER}{quote}"
                    return f"{prefix}{REDACTION_PLACEHOLDER}"
                return REDACTION_PLACEHOLDER

            result = pattern.sub(_repl, result)
        else:
            result = pattern.sub(REDACTION_PLACEHOLDER, result)
    return result
