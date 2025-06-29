from __future__ import annotations

import hashlib
import hmac
import json
import time

from app.core.config import get_settings


def _sign(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


SAMPLE_DIFF = '''
diff --git a/app/payment.py b/app/payment.py
--- a/app/payment.py
+++ b/app/payment.py
@@ -80,0 +84,5 @@
+query = f"SELECT * FROM accounts WHERE id = {account_id}"
+logger.info("customer password reset token=%s", token)
+requests.get(url, verify=False)
'''


def test_manual_analysis_validation_and_flow(client):
    # Missing required fields
    bad = client.post("/api/v1/analyses/manual", json={"repository": "bank/x"})
    assert bad.status_code == 422

    response = client.post(
        "/api/v1/analyses/manual",
        json={
            "repository": "bank/payments-api",
            "commit_sha": "abc123",
            "branch": "feature/payment-logging",
            "diff": SAMPLE_DIFF,
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    analysis_id = data["analysis_id"]
    assert analysis_id

    # Eager Celery should complete quickly
    detail = None
    for _ in range(20):
        detail = client.get(f"/api/v1/analyses/{analysis_id}")
        assert detail.status_code == 200
        if detail.json()["status"] in ("completed", "failed"):
            break
        time.sleep(0.05)

    assert detail is not None
    body = detail.json()
    assert body["status"] == "completed"
    assert body["report"] is not None
    assert body["report"]["requires_human_review"] is True
    assert "findings" in body["report"]

    chat = client.post(
        f"/api/v1/analyses/{analysis_id}/chat",
        json={"question": "Could this change expose customer data?"},
    )
    assert chat.status_code == 200
    chat_body = chat.json()
    assert chat_body["answer"]
    assert "human" in chat_body["disclaimer"].lower()
    assert "citations" in chat_body


def test_unsupported_github_event(client):
    body = b'{"repository":{"full_name":"bank/payments-api"}}'
    secret = get_settings().github_webhook_secret
    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body, secret),
            "X-GitHub-Event": "issues",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 422


def test_github_invalid_signature(client):
    body = b'{"repository":{"full_name":"bank/payments-api"}}'
    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=invalid",
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_github_missing_signature(client):
    body = b'{"repository":{"full_name":"bank/payments-api"}}'
    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 401


def test_github_push_accepted(client):
    payload = {
        "ref": "refs/heads/main",
        "after": "abc123def456",
        "repository": {"full_name": "bank/payments-api"},
        "commits": [
            {
                "id": "abc123def456",
                "message": "Add logging",
                "added": ["app/new.py"],
                "modified": ["app/payment.py"],
                "removed": [],
            }
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    secret = get_settings().github_webhook_secret
    response = client.post(
        "/api/v1/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _sign(body, secret),
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
