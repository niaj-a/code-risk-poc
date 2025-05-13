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
