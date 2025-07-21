import hashlib
import hmac

from app.core.security import is_repository_allowed, verify_github_signature


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_valid_github_signature():
    secret = "test-webhook-secret"
    body = b'{"ref":"refs/heads/main"}'
    assert verify_github_signature(body, _sign(secret, body), secret) is True


def test_invalid_github_signature():
    secret = "test-webhook-secret"
    body = b'{"ref":"refs/heads/main"}'
    assert (
        verify_github_signature(body, "sha256=deadbeef", secret) is False
    )


def test_missing_github_signature():
    secret = "test-webhook-secret"
    body = b'{"ref":"refs/heads/main"}'
    assert verify_github_signature(body, None, secret) is False
    assert verify_github_signature(body, "", secret) is False
    assert verify_github_signature(body, "sha1=abc", secret) is False


def test_repository_allowlist_empty_allows_all():
    assert is_repository_allowed("bank/payments-api", set()) is True


def test_repository_allowlist_enforced():
    allowed = {"bank/payments-api"}
    assert is_repository_allowed("bank/payments-api", allowed) is True
    assert is_repository_allowed("bank/other", allowed) is False
