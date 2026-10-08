import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from ci import sonarqube as sonar


PROJECT = "giangnamG_DevOps-Draft"
PROPERTIES = {"sonar.projectKey": PROJECT, "sonar.projectName": "DevOps-Draft"}
SUCCESS_ENV = {
    "LINT_OUTCOME": "success", "SERVER_OUTCOME": "success",
    "SCAN_OUTCOME": "success", "REPORT_OUTCOME": "success",
    "ENFORCE_QUALITY_GATE": "true", "GITHUB_REPOSITORY": "giangnamG/DevOps-Draft",
    "GITHUB_SHA": "abc123", "GITHUB_STEP_SUMMARY": "",
}


def analysis_api(*, php=True, task_status="SUCCESS"):
    api = Mock(spec=sonar.Api)
    api.password = "temporary-password"

    def request(endpoint, params):
        if endpoint == "ce/task":
            return {"task": {"status": task_status, "analysisId": "analysis-1"}}
        if endpoint == "qualitygates/project_status":
            return {"projectStatus": {"status": "ERROR", "conditions": [{
                "metricKey": "security_rating", "actualValue": "3",
                "comparator": "GT", "errorThreshold": "1", "status": "ERROR",
            }]}}
        if endpoint == "measures/component":
            return {"component": {"measures": [{"metric": "ncloc", "value": "12"}]}}
        raise AssertionError(endpoint)

    def pages(endpoint, field, params):
        if endpoint == "issues/search":
            values = [{"component": PROJECT + ":InlaneWeb/web/src/pages/login.php",
                       "line": 19, "rule": "php:S2077", "type": "VULNERABILITY",
                       "severity": "MAJOR", "message": '<script>alert("x")</script>'}]
        elif endpoint == "hotspots/search":
            values = [{"component": PROJECT + ":InlaneWeb/web/src/lib/db.php",
                       "line": 17, "vulnerabilityProbability": "HIGH",
                       "message": "Review SQL query", "securityCategory": "sql-injection"}]
        elif endpoint == "components/tree":
            values = [{"language": "php" if php else "css", "path": "sample.php"}]
        else:
            raise AssertionError(endpoint)
        return {"total": len(values), field: values}

    api.request.side_effect = request
    api.all_pages.side_effect = pages
    return api


class PaginationTests(unittest.TestCase):
    def test_every_page_is_exported(self):
        api = sonar.Api("http://localhost:9000")
        api.request = Mock(side_effect=[
            {"paging": {"total": 3}, "issues": [{"key": "1"}, {"key": "2"}]},
            {"paging": {"total": 3}, "issues": [{"key": "3"}]},
        ])
        result = api.all_pages("issues/search", "issues", {"componentKeys": PROJECT})
        self.assertEqual([item["key"] for item in result["issues"]], ["1", "2", "3"])
        self.assertEqual(api.request.call_args.args[1]["p"], 2)

    def test_incomplete_page_is_not_reported_as_success(self):
        api = sonar.Api("http://localhost:9000")
        api.request = Mock(return_value={"paging": {"total": 2}, "issues": []})
        with self.assertRaisesRegex(sonar.SonarError, "incomplete"):
            api.all_pages("issues/search", "issues", {})


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.reports = self.root / "reports"
        self.reports.mkdir()
        (self.root / ".scannerwork").mkdir()
        (self.root / ".scannerwork/report-task.txt").write_text("ceTaskId=task-1\n", encoding="utf-8")
        self.environment = patch.dict(os.environ, SUCCESS_ENV)
        self.environment.start()
        self.root_patch = patch.object(sonar, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.environment.stop()
        self.temporary.cleanup()

    def test_failed_gate_exports_all_reports_before_enforcement(self):
        self.assertEqual(sonar.make_report(analysis_api(), PROPERTIES, self.reports, 1), 0)
        for filename in ("report.html", "summary.md", "issues.json", "hotspots.json",
                         "metrics.json", "quality-gate.json", "metadata.json", "files.json"):
            self.assertTrue((self.reports / filename).is_file(), filename)
        self.assertEqual(json.loads((self.reports / "status.json").read_text())["quality_gate"], "ERROR")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sonar.check(self.reports), 1)
        os.environ["ENFORCE_QUALITY_GATE"] = "false"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sonar.check(self.reports), 0)

    def test_html_escapes_findings_and_links_to_exact_commit(self):
        sonar.make_report(analysis_api(), PROPERTIES, self.reports, 1)
        page = (self.reports / "report.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("/blob/abc123/InlaneWeb/web/src/pages/login.php#L19", page)
        self.assertNotIn("temporary-password", page)

    def test_zero_php_files_refuses_false_pass(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sonar.make_report(analysis_api(php=False), PROPERTIES, self.reports, 1), 1)
        status = json.loads((self.reports / "status.json").read_text())
        self.assertFalse(status["analysis_complete"])
        self.assertIn("no PHP files", status["error"])

    def test_server_processing_failure_still_creates_diagnostic_html(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code = sonar.make_report(analysis_api(task_status="FAILED"), PROPERTIES, self.reports, 1)
        self.assertEqual(code, 1)
        page = (self.reports / "report.html").read_text(encoding="utf-8")
        self.assertIn("UNAVAILABLE", page)
        self.assertIn("processing FAILED", page)

    def test_missing_scanner_metadata_still_creates_report(self):
        (self.root / ".scannerwork/report-task.txt").unlink()
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sonar.make_report(analysis_api(), PROPERTIES, self.reports, 1), 1)
        self.assertTrue((self.reports / "report.html").exists())

    def test_report_only_does_not_hide_lint_failure(self):
        sonar.make_report(analysis_api(), PROPERTIES, self.reports, 1)
        os.environ.update(ENFORCE_QUALITY_GATE="false", LINT_OUTCOME="failure")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sonar.check(self.reports), 1)

    def test_report_only_does_not_hide_missing_gate(self):
        sonar.save_json(self.reports / "status.json", {"analysis_complete": True, "quality_gate": "NONE"})
        os.environ["ENFORCE_QUALITY_GATE"] = "false"
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sonar.check(self.reports), 1)

    def test_analysis_timeout_is_not_a_pass(self):
        with self.assertRaisesRegex(sonar.SonarError, "Timed out"):
            sonar.wait_for_analysis(analysis_api(), "task-1", 0)


class BootstrapTests(unittest.TestCase):
    def test_credentials_are_not_written_into_report(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {"GITHUB_ENV": "", "GITHUB_ACTIONS": "false"}):
            reports = Path(temporary)
            api = Mock(spec=sonar.Api)

            def request(endpoint, params=None, **kwargs):
                if endpoint == "system/status":
                    return {"status": "UP"}
                if endpoint == "user_tokens/generate":
                    return {"token": "sqp_test-secret"}
                if endpoint == "server/version":
                    return "26.9.0"
                return {}

            api.request.side_effect = request
            with contextlib.redirect_stdout(io.StringIO()):
                sonar.bootstrap(api, PROPERTIES, reports, 1)
            data = (reports / "bootstrap.json").read_text()
            self.assertNotIn("sqp_test-secret", data)
            self.assertNotIn(os.environ["SONAR_ADMIN_PASSWORD"], data)
            self.assertEqual(os.environ["SONAR_TOKEN"], "sqp_test-secret")
            token_call = next(call for call in api.request.call_args_list if call.args[0] == "user_tokens/generate")
            self.assertEqual(token_call.args[1]["type"], "PROJECT_ANALYSIS_TOKEN")


if __name__ == "__main__":
    unittest.main()
