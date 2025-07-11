from app.schemas.analysis import AnalysisReport, RiskLevel
from app.services.mock_analyzer import analyze_diff


def test_sql_injection_detection():
    diff = '''
diff --git a/app/payment.py b/app/payment.py
--- a/app/payment.py
+++ b/app/payment.py
@@ -10,0 +11,1 @@
+query = f"SELECT * FROM accounts WHERE id = {account_id}"
'''
    report = analyze_diff(diff)
    assert isinstance(report, AnalysisReport)
    assert any(f.category == "sql_injection" for f in report.findings)
    assert report.requires_human_review is True


def test_sensitive_logging_detection():
    diff = '''
+++ b/app/logging_utils.py
@@ -1,0 +2,1 @@
+logger.info("customer account %s card=%s", customer_id, card_last4)
'''
    report = analyze_diff(diff)
    assert any(f.category == "sensitive_data_logging" for f in report.findings)


def test_tls_verification_detection():
    diff = '''
+++ b/app/client.py
@@ -5,0 +6,1 @@
+response = requests.get(url, verify=False)
'''
    report = analyze_diff(diff)
    assert any(f.category == "tls_verification" for f in report.findings)
    assert report.risk_level == RiskLevel.CRITICAL


def test_hardcoded_secret_detection():
    diff = '+api_key = "sk-abcdefghijklmnopqrstuvwxyz012345"\n'
    report = analyze_diff(diff)
    assert any(f.category == "secrets" for f in report.findings)


def test_shell_execution_detection():
    diff = '+subprocess.run(cmd, shell=True)\n'
    report = analyze_diff(diff)
    assert any(f.category == "command_injection" for f in report.findings)


def test_mock_analysis_result_schema():
    report = analyze_diff("+print('hello')\n")
    validated = AnalysisReport.model_validate(report.model_dump())
    assert validated.requires_human_review is True
    assert validated.summary
    assert isinstance(validated.findings, list)
    assert isinstance(validated.recommended_tests, list)
