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
    event_type: str
    raw_diff: str
    commit_messages: list[str] = field(default_factory=list)
    added_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    pr_title: str | None = None
    pr_body: str | None = None
    has_full_patch: bool = False


class DiffFetcher(Protocol):
    """Hook for a future GitHub App / ADO compare fetch. Not implemented here."""

    def fetch_compare_diff(
        self,
        repository: str,
        base_sha: str,
        head_sha: str,
    ) -> str: ...

    def fetch_pull_request_diff(self, repository: str, pr_number: int) -> str: ...


class StubDiffFetcher:
    def fetch_compare_diff(
        self,
        repository: str,
        base_sha: str,
        head_sha: str,
    ) -> str:
        raise NotImplementedError(
            f"compare diff not implemented ({repository} {base_sha}..{head_sha})"
