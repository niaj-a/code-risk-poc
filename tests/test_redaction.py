from app.services.redaction import REDACTION_PLACEHOLDER, redact_sensitive_content


def test_api_key_redaction():
    original = 'api_key = "sk-live-SUPER_SECRET_VALUE_12345"'
    redacted = redact_sensitive_content(original)
    assert "SUPER_SECRET_VALUE" not in redacted
    assert "sk-live" not in redacted
    assert REDACTION_PLACEHOLDER in redacted


def test_password_redaction():
    original = 'password: "Hunter2!BankSecret"'
    redacted = redact_sensitive_content(original)
    assert "Hunter2!BankSecret" not in redacted
    assert REDACTION_PLACEHOLDER in redacted


def test_bearer_token_redaction():
    token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"
    redacted = redact_sensitive_content(token)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
    assert REDACTION_PLACEHOLDER in redacted


def test_private_key_redaction():
    pem = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF6PZGBw=\n"
        "-----END RSA PRIVATE KEY-----"
    )
    redacted = redact_sensitive_content(pem)
    assert "MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn" not in redacted
    assert REDACTION_PLACEHOLDER in redacted


def test_connection_string_redaction():
    original = "postgresql://bankuser:SuperSecretPwd@db.internal:5432/payments"
    redacted = redact_sensitive_content(original)
    assert "SuperSecretPwd" not in redacted
    assert REDACTION_PLACEHOLDER in redacted


def test_payment_card_redaction():
    # Example Visa-like pattern (not a real card intended for charging)
    original = "card_number = 4111 1111 1111 1111"
    redacted = redact_sensitive_content(original)
    assert "4111 1111 1111 1111" not in redacted
    assert "4111111111111111" not in redacted.replace(" ", "")
    assert REDACTION_PLACEHOLDER in redacted


def test_jwt_like_redaction():
    jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    redacted = redact_sensitive_content(f"token={jwt}")
    assert "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c" not in redacted
