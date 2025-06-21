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
