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
