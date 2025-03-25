from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


METADATA_ONLY_MARKER = (
    "=== METADATA ONLY — not a complete code diff ===\n"
    "Webhook didn't include file patches. Don't invent changes.\n"
)


@dataclass
class ParsedGitHubEvent:
    repository: str
    commit_sha: str
    branch: str | None
