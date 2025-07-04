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
    assert response.status_code == 202
    assert response.json()["status"] == "queued"


def test_repository_allowlist(client, monkeypatch):
    monkeypatch.setenv("ALLOWED_REPOSITORIES", "bank/allowed-only")
    get_settings.cache_clear()

    # Recreate app so routes use updated settings via Depends(get_settings)
    from app.db import session as db_session
    from app.main import create_app

    application = create_app()

    def _override_get_db():
        db = db_session.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[db_session.get_db] = _override_get_db

    from fastapi.testclient import TestClient

    with TestClient(application) as local_client:
        response = local_client.post(
            "/api/v1/analyses/manual",
            json={
                "repository": "bank/payments-api",
                "commit_sha": "abc",
                "diff": "+print(1)\n",
            },
        )
        assert response.status_code == 403

        ok = local_client.post(
            "/api/v1/analyses/manual",
            json={
                "repository": "bank/allowed-only",
                "commit_sha": "abc",
                "diff": "+print(1)\n",
            },
        )
        assert ok.status_code == 202

    monkeypatch.setenv("ALLOWED_REPOSITORIES", "")
    get_settings.cache_clear()


def test_analysis_not_found(client):
    response = client.get("/api/v1/analyses/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_chat_before_completion(client):
    from app.db import session as db_session
    from app.db.models import Analysis, AnalysisStatusEnum

    db = db_session.SessionLocal()
    try:
        analysis = Analysis(
            repository="bank/payments-api",
            commit_sha="abc",
            branch="main",
            event_type="manual",
            status=AnalysisStatusEnum.queued,
            raw_diff="+x\n",
        )
