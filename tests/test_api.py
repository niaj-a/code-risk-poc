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
