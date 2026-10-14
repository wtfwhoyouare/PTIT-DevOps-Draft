"""Generate an HTML report and GitHub Step Summary from Semgrep JSON results."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMGREP_JSON = ROOT / "reports/semgrep/semgrep.json"
REPORT_HTML = ROOT / "reports/semgrep/report.html"
REPORT_MD = ROOT / "reports/semgrep/summary.md"


def main():
    if not SEMGREP_JSON.exists():
        print(f"Missing {SEMGREP_JSON}")
        return

    data = json.loads(SEMGREP_JSON.read_text(encoding="utf-8"))
    results = data.get("results", [])

    errors = [r for r in results if r.get("extra", {}).get("severity") == "ERROR"]
    warnings = [r for r in results if r.get("extra", {}).get("severity") == "WARNING"]
    infos = [r for r in results if r.get("extra", {}).get("severity") == "INFO"]

    # Markdown Summary
    md_lines = [
        "## 🛡️ Semgrep Security SAST Report",
        "",
        f"**Total Security Findings:** {len(results)}",
        f"- 🔴 **High / Critical (ERROR):** {len(errors)}",
        f"- 🟡 **Medium (WARNING):** {len(warnings)}",
        f"- 🔵 **Low / Info (INFO):** {len(infos)}",
        "",
        "| Severity | Rule ID | File:Line | OWASP / CWE | Message |",
        "| --- | --- | --- | --- | --- |",
    ]

    for r in results:
        check_id = r.get("check_id", "unknown").split(".")[-1]
        sev = r.get("extra", {}).get("severity", "INFO")
        path = r.get("path", "")
        line = r.get("start", {}).get("line", 0)
        msg = r.get("extra", {}).get("message", "").replace("\n", " ").strip()
        metadata = r.get("extra", {}).get("metadata", {})
        owasp = metadata.get("owasp", metadata.get("cwe", "Security"))
        if isinstance(owasp, list):
            owasp = owasp[0]
        md_lines.append(f"| **{sev}** | `{check_id}` | `{path}:{line}` | {owasp} | {msg} |")

    summary_content = "\n".join(md_lines)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(summary_content, encoding="utf-8")

    # If running in GitHub Actions, write to step summary
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(summary_content + "\n")

    # Generate standalone HTML report
    rows_html = []
    for r in results:
        check_id = html.escape(r.get("check_id", "unknown").split(".")[-1])
        sev = r.get("extra", {}).get("severity", "INFO")
        sev_color = "#ef4444" if sev == "ERROR" else ("#f59e0b" if sev == "WARNING" else "#3b82f6")
        path = html.escape(r.get("path", ""))
        line = r.get("start", {}).get("line", 0)
        msg = html.escape(r.get("extra", {}).get("message", "").strip())
        code_snip = html.escape(r.get("extra", {}).get("lines", "").strip())
        meta = r.get("extra", {}).get("metadata", {})
        cwe = html.escape(str(meta.get("cwe", "")))
        owasp = html.escape(str(meta.get("owasp", "")))

        rows_html.append(f"""
        <tr style="border-bottom: 1px solid #334155;">
            <td style="padding: 12px;"><span style="background:{sev_color};color:#fff;padding:4px 8px;border-radius:4px;font-weight:bold;font-size:12px;">{sev}</span></td>
            <td style="padding: 12px;font-family:monospace;font-weight:600;color:#38bdf8;">{check_id}</td>
            <td style="padding: 12px;font-family:monospace;color:#94a3b8;">{path}:{line}</td>
            <td style="padding: 12px;font-size:13px;color:#cbd5e1;"><strong>{owasp}</strong><br><small style="color:#64748b;">{cwe}</small></td>
            <td style="padding: 12px;font-size:13px;color:#f1f5f9;">{msg}<pre style="margin-top:6px;background:#0f172a;padding:8px;border-radius:4px;overflow-x:auto;color:#a5f3fc;font-size:12px;"><code>{code_snip}</code></pre></td>
        </tr>
        """)

    html_page = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Semgrep Security SAST Report - IlFreight Logistics</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f8fafc; margin: 0; padding: 24px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px; }}
        .badge {{ padding: 8px 16px; border-radius: 9999px; font-weight: bold; font-size: 14px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #131c2e; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; }}
        .card-num {{ font-size: 28px; font-weight: bold; margin-top: 8px; }}
        table {{ width: 100%; border-collapse: collapse; background: #131c2e; border: 1px solid #1e293b; border-radius: 8px; }}
        th {{ background: #1e293b; color: #94a3b8; text-align: left; padding: 12px; font-size: 13px; text-transform: uppercase; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1 style="margin:0 0 8px 0;font-size:24px;">🛡️ Báo Cáo An Toàn Phần Mềm (Semgrep SAST)</h1>
            <p style="margin:0;color:#94a3b8;font-size:14px;">Ứng dụng: IlFreight Logistics (InlaneWeb/web/src)</p>
        </div>
        <div>
            <span class="badge" style="background: {'#ef4444' if errors else '#22c55e'}; color: white;">
                {'PHÁT HIỆN LỖ HỔNG NGUY HIỂM' if errors else 'AN TOÀN'}
            </span>
        </div>
    </div>

    <div class="stats">
        <div class="card">
            <div style="color:#94a3b8;font-size:13px;">TỔNG SỐ LỖ HỔNG</div>
            <div class="card-num" style="color:#f8fafc;">{len(results)}</div>
        </div>
        <div class="card">
            <div style="color:#ef4444;font-size:13px;">NGHIÊM TRỌNG (ERROR)</div>
            <div class="card-num" style="color:#ef4444;">{len(errors)}</div>
        </div>
        <div class="card">
            <div style="color:#f59e0b;font-size:13px;">CẢNH BÁO (WARNING)</div>
            <div class="card-num" style="color:#f59e0b;">{len(warnings)}</div>
        </div>
        <div class="card">
            <div style="color:#3b82f6;font-size:13px;">THÔNG TIN (INFO)</div>
            <div class="card-num" style="color:#3b82f6;">{len(infos)}</div>
        </div>
    </div>

    <h2 style="font-size:18px;margin:24px 0 12px 0;">Chi Tiết Các Lỗ Hổng Bảo Mật</h2>
    <table>
        <thead>
            <tr>
                <th style="width: 100px;">Mức Độ</th>
                <th style="width: 220px;">Rule ID</th>
                <th style="width: 200px;">Vị Trí (File:Line)</th>
                <th style="width: 220px;">Phân Loại (OWASP/CWE)</th>
                <th>Mô Tả & Đoạn Mã Vi Phạm</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
    </table>
</div>
</body>
</html>
"""
    REPORT_HTML.write_text(html_page, encoding="utf-8")
    print(f"Generated Semgrep reports: {REPORT_HTML} and {REPORT_MD}")


if __name__ == "__main__":
    main()
