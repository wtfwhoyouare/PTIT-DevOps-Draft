"""Bootstrap an ephemeral SonarQube instance and export a standalone report.

Python standard library only. Credentials remain in the job environment, never
in reports. Report generation and gate enforcement are deliberately separate.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
METRICS = (
    "ncloc", "files", "bugs", "vulnerabilities", "code_smells",
    "security_hotspots", "security_hotspots_reviewed", "security_rating",
    "reliability_rating", "sqale_rating", "duplicated_lines_density", "coverage",
)
LIMITATION = (
    "Community Build does not provide the full cross-function/cross-file "
    "injection analysis available in commercial editions. A passing gate or "
    "zero vulnerabilities does not establish that this intentionally vulnerable "
    "SQL injection lab is secure. Coverage is not measured: no PHPUnit report "
    "is configured. This is a static export, not a persistent SonarQube dashboard."
)


class SonarError(RuntimeError):
    pass


def redact(value: str) -> str:
    for name in ("SONAR_TOKEN", "SONAR_ADMIN_PASSWORD"):
        secret = os.environ.get(name)
        if secret:
            value = value.replace(secret, "[REDACTED]")
    return value


class Api:
    def __init__(self, host: str, token: str = "", password: str = ""):
        self.host = host.rstrip("/")
        self.token = token
        self.password = password

    def request(self, endpoint: str, params: dict | None = None, *, post=False):
        encoded = urlencode(params or {}).encode()
        url = self.host + "/api/" + endpoint
        if not post and encoded:
            url += "?" + encoded.decode()
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        elif self.password:
            auth = base64.b64encode(("admin:" + self.password).encode()).decode()
            headers["Authorization"] = "Basic " + auth
        if post:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = Request(url, data=encoded if post else None, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = redact(exc.read().decode("utf-8", errors="replace"))[:500]
            raise SonarError(f"API {endpoint}: HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise SonarError(f"API {endpoint}: {redact(str(exc))}") from exc
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            if endpoint == "server/version":
                return body.strip()
            raise SonarError(f"API {endpoint} did not return JSON")

    def all_pages(self, endpoint: str, field: str, params: dict):
        items = []
        for page in range(1, 101):
            payload = self.request(endpoint, {**params, "p": page, "ps": 500})
            if field not in payload:
                raise SonarError(f"API {endpoint}: missing {field}")
            batch = payload[field]
            items.extend(batch)
            total = payload.get("paging", {}).get("total", payload.get("total"))
            if total is None:
                raise SonarError(f"API {endpoint}: missing pagination total")
            if len(items) >= total:
                return {"total": total, field: items}
            if not batch:
                raise SonarError(f"API {endpoint}: incomplete pagination")
        raise SonarError(f"API {endpoint}: pagination limit exceeded; export incomplete")


def read_properties(path: Path) -> dict[str, str]:
    return {
        key.strip(): value.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
        for key, value in [line.split("=", 1)]
    }


def save_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def job_secret(name: str, value: str):
    # Mask before using the value or appending it to the Actions environment.
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("::add-mask::" + value, flush=True)
    os.environ[name] = value
    environment_file = os.environ.get("GITHUB_ENV")
    if environment_file:
        with open(environment_file, "a", encoding="utf-8") as stream:
            stream.write(f"{name}={value}\n")


def bootstrap(api: Api, properties: dict, report_dir: Path, timeout: int):
    deadline = time.monotonic() + timeout
    print("Waiting for SonarQube to become UP...", flush=True)
    last_status = "not reachable"
    while time.monotonic() < deadline:
        try:
            status = api.request("system/status")
            last_status = status.get("status", "unknown")
            if last_status == "UP":
                break
        except SonarError:
            pass
        time.sleep(5)
    else:
        raise SonarError(f"SonarQube startup timed out (last status: {last_status})")

    # Only for the brand-new, loopback-bound server created by this workflow.
    api.password = "admin"
    admin_password = secrets.token_urlsafe(32) + "!Aa1@"
    job_secret("SONAR_ADMIN_PASSWORD", admin_password)
    api.request("users/change_password", {
        "login": "admin", "previousPassword": "admin", "password": admin_password,
    }, post=True)
    api.password = admin_password
    project = properties["sonar.projectKey"]
    api.request("projects/create", {
        "project": project, "name": properties["sonar.projectName"],
        "mainBranch": "main", "visibility": "private",
    }, post=True)
    gate = json.loads((ROOT / "ci/sonarqube-quality-gate.json").read_text(encoding="utf-8"))
    api.request("qualitygates/create", {"name": gate["name"]}, post=True)
    for condition in gate["conditions"]:
        api.request("qualitygates/create_condition", {
            "gateName": gate["name"], **condition,
        }, post=True)
    api.request("qualitygates/select", {
        "projectKey": project, "gateName": gate["name"],
    }, post=True)
    token = api.request("user_tokens/generate", {
        "name": "ci-scan-" + os.environ.get("GITHUB_RUN_ID", secrets.token_hex(6)),
        "type": "PROJECT_ANALYSIS_TOKEN", "projectKey": project,
    }, post=True)["token"]
    job_secret("SONAR_TOKEN", token)
    save_json(report_dir / "bootstrap.json", {
        "project_key": project, "server_version": api.request("server/version"),
        "image": os.environ.get("SONAR_IMAGE", ""), "quality_gate": gate,
        "database": "ephemeral H2", "experience": "Standard",
    })
    print(f"Created temporary project {project} and overall-code quality gate.")


def wait_for_analysis(api: Api, task_id: str, timeout: int) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        task = api.request("ce/task", {"id": task_id})["task"]
        status = task["status"]
        if status == "SUCCESS":
            if not task.get("analysisId"):
                raise SonarError("Completed task has no analysisId")
            return task
        if status in ("FAILED", "CANCELED"):
            raise SonarError(f"Analysis processing {status}: {task.get('errorMessage', '')}")
        if status not in ("PENDING", "IN_PROGRESS"):
            raise SonarError(f"Unexpected analysis processing status: {status}")
        time.sleep(3)
    raise SonarError("Timed out waiting for server-side analysis processing")


def collect(api: Api, properties: dict, report_dir: Path, timeout: int) -> dict:
    project = properties["sonar.projectKey"]
    metadata_file = ROOT / ".scannerwork/report-task.txt"
    if not metadata_file.is_file():
        raise SonarError("Scanner did not produce .scannerwork/report-task.txt")
    task_id = read_properties(metadata_file).get("ceTaskId")
    if not task_id:
        raise SonarError("Scanner metadata has no ceTaskId")
    task = wait_for_analysis(api, task_id, timeout)
    save_json(report_dir / "analysis-task.json", {"task": task})
    gate = api.request("qualitygates/project_status", {"analysisId": task["analysisId"]})
    if gate.get("projectStatus", {}).get("status") not in ("OK", "ERROR"):
        raise SonarError("Quality gate result is absent or not evaluated")
    save_json(report_dir / "quality-gate.json", gate)
    metrics = api.request("measures/component", {
        "component": project, "metricKeys": ",".join(METRICS),
    })
    save_json(report_dir / "metrics.json", metrics)
    issues = api.all_pages("issues/search", "issues", {"componentKeys": project})
    save_json(report_dir / "issues.json", issues)
    hotspots = api.all_pages("hotspots/search", "hotspots", {"projectKey": project})
    save_json(report_dir / "hotspots.json", hotspots)
    files = api.all_pages("components/tree", "components", {
        "component": project, "qualifiers": "FIL",
    })
    save_json(report_dir / "files.json", files)
    php_files = sum(item.get("language") == "php" for item in files["components"])
    measures = {item["metric"]: item.get("value") for item in metrics["component"]["measures"]}
    if php_files == 0 or float(measures.get("ncloc") or 0) <= 0:
        raise SonarError("Analysis contains no PHP files or no source lines; refusing a false pass")
    return {"gate": gate["projectStatus"], "measures": measures,
            "issues": issues["issues"], "hotspots": hotspots["hotspots"],
            "php_files": php_files}


def source_link(component: str, line, project: str, repository: str, sha: str) -> str:
    if not repository or not sha:
        return ""
    path = component.removeprefix(project + ":")
    url = "https://github.com/" + quote(repository, safe="/") + "/blob/" + quote(sha, safe="")
    url += "/" + quote(path, safe="/")
    if isinstance(line, int) and line > 0:
        url += f"#L{line}"
    return url


def render_report(report_dir: Path, metadata: dict, result: dict | None, error: str = ""):
    escape = lambda value: html.escape(str(value), quote=True)
    result = result or {"gate": {}, "measures": {}, "issues": [], "hotspots": [], "php_files": 0}
    gate_status = result["gate"].get("status", "UNAVAILABLE")
    issue_counts = Counter(item.get("severity", "UNKNOWN") for item in result["issues"])
    summary = [
        "## SonarQube report", "", f"**Quality Gate: {gate_status}**", "",
        f"Commit: `{metadata['commit']}`", "",
        f"PHP lint: **{metadata['lint']}** · Scanner: **{metadata['scanner']}**", "",
        f"PHP files analyzed: **{result['php_files']}** · Issues: **{len(result['issues'])}** "
        f"· Security hotspots: **{len(result['hotspots'])}**", "",
        "Gate scope: overall code; no historical/new-code baseline.", "",
        "Gate enforcement: " + ("enabled" if metadata["enforce_quality_gate"] else "report-only") + ".", "",
    ]
    if issue_counts:
        summary.extend(["| Severity | Issues |", "| --- | ---: |"])
        summary.extend(f"| {severity} | {count} |" for severity, count in sorted(issue_counts.items()))
        summary.append("")

    if result["issues"]:
        summary.extend([
            f"### Chi tiết danh sách tất cả Issues ({len(result['issues'])})",
            "",
            "| Mức độ | Phân loại | Vị trí (Tệp:Dòng) | Rule ID | Chi tiết vi phạm |",
            "| --- | --- | --- | --- | --- |",
        ])
        for item in result["issues"]:
            component = item.get("component", "")
            path = component.removeprefix(metadata.get("project_key", "") + ":")
            line = item.get("line", item.get("textRange", {}).get("startLine", ""))
            link = source_link(component, line, metadata.get("project_key", ""), metadata.get("repository", ""), metadata.get("commit", ""))
            loc = escape(path + (f":{line}" if line else ""))
            if link:
                loc = f"[{loc}]({link})"
            sev = escape(item.get("severity", ""))
            itype = escape(item.get("type", ""))
            rule = escape(item.get("rule", ""))
            msg = escape(item.get("message", "")).replace("\n", " ").replace("|", "&#124;")
            summary.append(f"| **{sev}** | {itype} | {loc} | `{rule}` | {msg} |")
        summary.append("")

    if result["hotspots"]:
        summary.extend([
            f"### Chi tiết Security Hotspots ({len(result['hotspots'])})",
            "",
            "| Mức độ | Phân loại | Vị trí (Tệp:Dòng) | Rule ID | Chi tiết vi phạm |",
            "| --- | --- | --- | --- | --- |",
        ])
        for item in result["hotspots"]:
            component = item.get("component", "")
            path = component.removeprefix(metadata.get("project_key", "") + ":")
            line = item.get("line", item.get("textRange", {}).get("startLine", ""))
            link = source_link(component, line, metadata.get("project_key", ""), metadata.get("repository", ""), metadata.get("commit", ""))
            loc = escape(path + (f":{line}" if line else ""))
            if link:
                loc = f"[{loc}]({link})"
            prob = escape(item.get("vulnerabilityProbability", ""))
            cat = escape(item.get("securityCategory", ""))
            rule = escape(item.get("ruleKey", ""))
            msg = escape(item.get("message", "")).replace("\n", " ").replace("|", "&#124;")
            summary.append(f"| **{prob}** | {cat} | {loc} | `{rule}` | {msg} |")
        summary.append("")

    if error:
        summary.extend(["### Analysis/export error", "", escape(error), ""])
    conditions = result["gate"].get("conditions", [])
    if conditions:
        summary.extend(["| Gate metric | Value | Failure condition | Status |", "| --- | ---: | --- | --- |"])
        for condition in conditions:
            summary.append("| " + " | ".join(escape(value).replace("|", "&#124;") for value in (
                condition["metricKey"], condition.get("actualValue", "N/A"),
                condition.get("comparator", "") + " " + condition.get("errorThreshold", ""),
                condition.get("status", ""),
            )) + " |")
        summary.append("")
    summary.extend([
        "Download the **sonarqube-report-...** artifact for this run, extract it, and open **report.html**.", "",
        LIMITATION, "",
    ])
    summary_text = "\n".join(summary)
    (report_dir / "summary.md").write_text(summary_text, encoding="utf-8")
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as stream:
            stream.write(summary_text)

    def table(headers, rows):
        head = "".join("<th>" + escape(value) + "</th>" for value in headers)
        body = "".join("<tr>" + "".join("<td>" + cell + "</td>" for cell in row) + "</tr>" for row in rows)
        return "<table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table>"

    def finding_rows(items, hotspot=False):
        rows = []
        for item in items:
            component = item.get("component", "")
            path = component.removeprefix(metadata["project_key"] + ":")
            line = item.get("line", item.get("textRange", {}).get("startLine", ""))
            link = source_link(component, line, metadata["project_key"], metadata["repository"], metadata["commit"])
            location = escape(path + (f":{line}" if line else ""))
            if link:
                location = '<a href="' + escape(link) + '">' + location + "</a>"
            rows.append([
                escape(item.get("vulnerabilityProbability" if hotspot else "severity", "")),
                escape(item.get("securityCategory" if hotspot else "type", "")),
                location, escape(item.get("ruleKey" if hotspot else "rule", "")),
                escape(item.get("message", "")),
            ])
        return rows

    metric_rows = [[escape(key), escape(value)] for key, value in sorted(result["measures"].items())]
    condition_rows = [[escape(condition.get(key, "N/A")) for key in
                       ("metricKey", "actualValue", "comparator", "errorThreshold", "status")]
                      for condition in conditions]
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DevOps-Draft · SonarQube report</title><style>
body{font:15px/1.6 system-ui,sans-serif;max-width:1280px;margin:32px auto;padding:0 20px;color:#172033}
h1,h2{line-height:1.25}a{color:#174da8}table{border-collapse:collapse;width:100%;margin:20px 0;overflow-wrap:anywhere}
th,td{padding:10px;text-align:left;border:1px solid #d7deea;vertical-align:top}th{background:#eef2f8}
.note{padding:16px;background:#fff5dc;border-left:4px solid #a96b00}.status{font-weight:700;font-size:22px}
code{overflow-wrap:anywhere}details{margin:16px 0}pre{white-space:pre-wrap}</style></head><body>
<h1>DevOps-Draft · SonarQube report</h1>"""
    page += '<p class="status">Quality Gate: ' + escape(gate_status) + "</p>"
    page += "<p>Commit: <code>" + escape(metadata["commit"]) + "</code><br>Generated: " + escape(metadata["generated_at"]) + "</p>"
    page += "<p>PHP lint: " + escape(metadata["lint"]) + "; scanner: " + escape(metadata["scanner"]) + "; PHP files analyzed: " + str(result["php_files"]) + "</p>"
    page += '<p class="note">' + escape(LIMITATION) + "</p>"
    if error:
        page += "<h2>Analysis/export error</h2><pre>" + escape(error) + "</pre>"
    page += "<h2>Quality Gate — overall code</h2>" + table(["Metric", "Value", "Operator", "Failure threshold", "Status"], condition_rows)
    page += "<h2>Metrics</h2>" + table(["Metric", "Value"], metric_rows)
    page += f"<h2>Issues ({len(result['issues'])})</h2>" + table(["Severity", "Type", "Source", "Rule", "Message"], finding_rows(result["issues"]))
    page += f"<h2>Security hotspots ({len(result['hotspots'])})</h2>" + table(["Probability", "Category", "Source", "Rule", "Message"], finding_rows(result["hotspots"], hotspot=True))
    page += "<details><summary>Run metadata</summary><pre>" + escape(json.dumps(metadata, indent=2, ensure_ascii=False)) + "</pre></details></body></html>"
    (report_dir / "report.html").write_text(page, encoding="utf-8")


def make_report(api: Api, properties: dict, report_dir: Path, timeout: int) -> int:
    metadata = {
        "project_key": properties["sonar.projectKey"],
        "repository": os.environ.get("GITHUB_REPOSITORY", ""),
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        "image": os.environ.get("SONAR_IMAGE", ""),
        "scanner_version": os.environ.get("SONAR_SCANNER_VERSION", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lint": os.environ.get("LINT_OUTCOME", "unknown"),
        "scanner": os.environ.get("SCAN_OUTCOME", "unknown"),
        "enforce_quality_gate": os.environ.get("ENFORCE_QUALITY_GATE", "true").lower() == "true",
        "snapshot": False,
    }
    save_json(report_dir / "metadata.json", metadata)
    result = None
    error = ""
    try:
        if os.environ.get("SERVER_OUTCOME") != "success":
            raise SonarError("SonarQube startup/bootstrap failed or was skipped; see server.log")
        if metadata["scanner"] != "success":
            raise SonarError("Scanner failed or was skipped; see the Analyze source job log")
        if not api.password:
            raise SonarError("Temporary report API credential is unavailable")
        result = collect(api, properties, report_dir, timeout)
    except (SonarError, KeyError, ValueError, OSError) as exc:
        error = redact(str(exc))
        print("Report unavailable: " + error, file=sys.stderr)
    save_json(report_dir / "status.json", {
        "analysis_complete": result is not None,
        "quality_gate": result["gate"]["status"] if result else "UNAVAILABLE",
        "error": error,
    })
    render_report(report_dir, metadata, result, error)
    return 1 if error else 0


def check(report_dir: Path) -> int:
    failed = [name for name in ("LINT", "SERVER", "SCAN", "REPORT")
              if os.environ.get(name + "_OUTCOME") != "success"]
    if failed:
        print("Pipeline execution failure: " + ", ".join(failed), file=sys.stderr)
        return 1
    status_file = report_dir / "status.json"
    if not status_file.exists():
        print("Missing report status", file=sys.stderr)
        return 1
    status = json.loads(status_file.read_text(encoding="utf-8"))
    if not status.get("analysis_complete") or status.get("quality_gate") not in ("OK", "ERROR"):
        print("Analysis/gate did not complete", file=sys.stderr)
        return 1
    if status["quality_gate"] == "ERROR":
        if os.environ.get("ENFORCE_QUALITY_GATE", "true").lower() == "true":
            print("Quality Gate FAILED. Reports were exported before this check.", file=sys.stderr)
            return 1
        print("Quality Gate FAILED; report-only mode explicitly selected.")
    else:
        print("Quality Gate PASSED.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("bootstrap", "report", "check"))
    parser.add_argument("--timeout", type=int, default=420)
    args = parser.parse_args()
    report_dir = Path(os.environ.get("REPORT_DIR", str(ROOT / "reports/sonarqube")))
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        if args.command == "check":
            return check(report_dir)
        properties = read_properties(ROOT / "sonar-project.properties")
        api = Api(os.environ.get("SONAR_HOST_URL", "http://127.0.0.1:9000"))
        if args.command == "bootstrap":
            bootstrap(api, properties, report_dir, args.timeout)
            return 0
        # The scan uses a project token. Export requires Browse permission,
        # so it uses the temporary admin password instead, never the scan token.
        api.password = os.environ.get("SONAR_ADMIN_PASSWORD", "")
        return make_report(api, properties, report_dir, args.timeout)
    except (SonarError, KeyError, ValueError, OSError) as exc:
        print(redact(str(exc)), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
