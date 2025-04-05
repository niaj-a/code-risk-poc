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
        )
        else:
            commit_sha = "unknown"

    ref = str(payload.get("ref") or "")
    branch = ref.removeprefix("refs/heads/") if ref.startswith("refs/heads/") else ref or None

    commit_messages: list[str] = []
    added: list[str] = []
    modified: list[str] = []
    removed: list[str] = []

    for commit in payload.get("commits") or []:
        msg = commit.get("message")
        if msg:
            commit_messages.append(str(msg))
        added.extend(str(f) for f in (commit.get("added") or []))
        modified.extend(str(f) for f in (commit.get("modified") or []))
        removed.extend(str(f) for f in (commit.get("removed") or []))

    def _bullets(items: list[str]) -> list[str]:
        return [f"  - {item}" for item in items] if items else ["  - (none)"]

    lines = [
        METADATA_ONLY_MARKER,
        "Event: push",
        f"Repository: {repository}",
        f"Commit SHA: {commit_sha}",
        f"Branch: {branch or 'unknown'}",
        "Commit messages:",
        *_bullets(commit_messages),
        "Added files:",
        *_bullets(sorted(set(added))),
        "Modified files:",
        *_bullets(sorted(set(modified))),
        "Removed files:",
        *_bullets(sorted(set(removed))),
    ]

    return ParsedGitHubEvent(
        repository=repository,
        commit_sha=commit_sha,
        branch=branch,
        event_type="push",
        raw_diff="\n".join(lines),
        commit_messages=commit_messages,
        added_files=sorted(set(added)),
        modified_files=sorted(set(modified)),
        removed_files=sorted(set(removed)),
        has_full_patch=False,
    )


def _parse_pull_request(payload: dict[str, Any]) -> ParsedGitHubEvent:
    repository = _repo_full_name(payload)
    pr = payload.get("pull_request") or {}
    head = pr.get("head") or {}
    commit_sha = str(head.get("sha") or "")
    branch = head.get("ref")
    title = pr.get("title")
    body = pr.get("body")

    if not commit_sha:
        raise ValueError("Pull request payload missing pull_request.head.sha")

    lines = [
        METADATA_ONLY_MARKER,
        "Event: pull_request",
        f"Action: {payload.get('action', 'unknown')}",
        f"Repository: {repository}",
