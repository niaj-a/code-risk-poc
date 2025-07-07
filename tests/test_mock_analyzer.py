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
