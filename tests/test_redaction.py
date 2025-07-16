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
