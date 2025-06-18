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
