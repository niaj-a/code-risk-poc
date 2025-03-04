import hashlib
import hmac


def verify_github_signature(
    payload: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    """GitHub X-Hub-Signature-256 check (sha256=<hex>)."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    provided = signature_header.removeprefix("sha256=")
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided, expected)


def is_repository_allowed(repository: str, allowed: set[str]) -> bool:
    # empty allowlist = open (handy locally)
    if not allowed:
        return True
    return repository in allowed
