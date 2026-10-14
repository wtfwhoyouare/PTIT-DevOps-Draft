"""Generate an HTML report and GitHub Step Summary with explicit SOURCE and SINK traces."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
SEMGREP_JSON = ROOT / "reports/semgrep/semgrep.json"
REPORT_HTML = ROOT / "reports/semgrep/report.html"
REPORT_MD = ROOT / "reports/semgrep/summary.md"


def extract_source_and_sink(path_str: str, line_no: int, trace_data: dict | None = None):
    """Extract explicit Source and Sink code snippets with line numbers."""
    source_info = {"file": path_str, "lines": [], "desc": "User Input (HTTP Request / Parameters)"}
    sink_info = {"file": path_str, "lines": [], "desc": "Execution Sink (SQL Query / Unescaped Output)"}

    # 1. If Semgrep provided official dataflow_trace, extract from it
    if trace_data and isinstance(trace_data, dict):
        src_node = trace_data.get("taint_source", {})
        sink_node = trace_data.get("taint_sink", {})
        if src_node and src_node.get("content"):
            source_info["lines"] = [(src_node.get("start", {}).get("line", line_no), src_node.get("content").strip())]
        if sink_node and sink_node.get("content"):
            sink_info["lines"] = [(sink_node.get("start", {}).get("line", line_no), sink_node.get("content").strip())]

    # 2. Extract directly from local source file for 100% accurate, complete code
    file_path = ROOT / path_str
    if file_path.exists():
        raw_lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        idx = line_no - 1

        # Sink extraction (the target line + any immediately following query execution line)
        if not sink_info["lines"] and 0 <= idx < len(raw_lines):
            sink_lines = [(idx + 1, raw_lines[idx].strip())]
            if idx + 1 < len(raw_lines):
                next_line = raw_lines[idx + 1].strip()
                if any(w in next_line.lower() for w in ("query", "exec", "mysqli", "echo", "$row", "$res", "stmt")):
                    sink_lines.append((idx + 2, next_line))
            sink_info["lines"] = sink_lines

        # Source extraction (look backwards up to 35 lines for $_GET, $_POST, $_REQUEST, $_COOKIE, etc.)
        if not source_info["lines"]:
            src_lines = []
            for i in range(max(0, idx - 35), idx):
                l_strip = raw_lines[i].strip()
                if l_strip.startswith(("//", "*", "/*", "#")):
                    continue
                if any(v in l_strip for v in ("$_GET", "$_POST", "$_REQUEST", "$_COOKIE", "$_SERVER")):
                    src_lines.append((i + 1, l_strip))
            if src_lines:
                source_info["lines"] = src_lines
            elif 0 <= idx < len(raw_lines):
                source_info["lines"] = [(idx + 1, raw_lines[idx].strip())]

    return source_info, sink_info


def main():
    if not SEMGREP_JSON.exists():
        print(f"Missing {SEMGREP_JSON}")
        return

    data = json.loads(SEMGREP_JSON.read_text(encoding="utf-8"))
    results = data.get("results", [])

    errors = [r for r in results if r.get("extra", {}).get("severity") == "ERROR"]
    warnings = [r for r in results if r.get("extra", {}).get("severity") == "WARNING"]
    infos = [r for r in results if r.get("extra", {}).get("severity") == "INFO"]

    # Build detailed findings data
    findings = []
    for r in results:
        check_id = r.get("check_id", "unknown")
        sev = r.get("extra", {}).get("severity", "INFO")
        path = r.get("path", "")
        line = r.get("start", {}).get("line", 0)
        msg = r.get("extra", {}).get("message", "").replace("\n", " ").strip()
        meta = r.get("extra", {}).get("metadata", {})
        owasp = meta.get("owasp", "Security")
        if isinstance(owasp, list):
            owasp = owasp[0]
        cwe = meta.get("cwe", "")
        if isinstance(cwe, list):
            cwe = cwe[0]

        dataflow_trace = r.get("extra", {}).get("dataflow_trace")
        src, snk = extract_source_and_sink(path, line, dataflow_trace)

        findings.append({
            "check_id": check_id,
            "severity": sev,
            "path": path,
            "line": line,
            "message": msg,
            "owasp": owasp,
            "cwe": cwe,
            "source": src,
            "sink": snk,
        })

    # 1. Generate GitHub Step Summary (Markdown)
    md_lines = [
        "## 🛡️ Semgrep Community Security SAST Report (Chi Tiết SOURCE & SINK)",
        "",
        "> Phân tích an toàn mã nguồn sử dụng bộ rulesets chuẩn của cộng đồng Semgrep Registry (`p/owasp-top-ten`, `p/php`, `p/security-audit`, `p/cwe-top-25`).",
        "",
        f"**Tổng số phát hiện:** {len(findings)} | 🔴 **High/Critical (ERROR):** {len(errors)} | 🟡 **Medium (WARNING):** {len(warnings)}",
        "",
    ]

    for idx, f in enumerate(findings, 1):
        sev_icon = "🔴" if f["severity"] == "ERROR" else "🟡"
        md_lines.append(f"### {idx}. {sev_icon} [{f['severity']}] `{f['check_id']}`")
        md_lines.append(f"- **Vị trí:** `{f['path']}:{f['line']}`")
        md_lines.append(f"- **Phân loại:** **{f['owasp']}** | *{f['cwe']}*")
        md_lines.append(f"- **Mô tả:** {f['message']}")
        
        # Source box
        src_code = "\n".join(f"{l_num}: {code}" for l_num, code in f["source"]["lines"])
        md_lines.append("- **🟡 SOURCE (Nguồn dữ liệu người dùng nhập):**")
        md_lines.append(f"```php\n{src_code}\n```")

        # Sink box
        snk_code = "\n".join(f"{l_num}: {code}" for l_num, code in f["sink"]["lines"])
        md_lines.append("- **🔴 SINK (Điểm kích hoạt / Thực thi câu lệnh SQL nguy hiểm):**")
        md_lines.append(f"```php\n{snk_code}\n```")
        md_lines.append("---")

    summary_content = "\n".join(md_lines)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(summary_content, encoding="utf-8")

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as sm_file:
            sm_file.write(summary_content + "\n")

    # 2. Generate Standalone HTML Report with clear Source & Sink cards
    cards_html = []
    for idx, f in enumerate(findings, 1):
        sev = f["severity"]
        sev_color = "#ef4444" if sev == "ERROR" else ("#f59e0b" if sev == "WARNING" else "#3b82f6")
        check_id = html.escape(f["check_id"])
        path = html.escape(f["path"])
        line = f["line"]
        owasp = html.escape(str(f["owasp"]))
        cwe = html.escape(str(f["cwe"]))
        msg = html.escape(f["message"])

        src_lines_html = html.escape("\n".join(f"{l_num:3d} | {code}" for l_num, code in f["source"]["lines"]))
        snk_lines_html = html.escape("\n".join(f"{l_num:3d} | {code}" for l_num, code in f["sink"]["lines"]))

        cards_html.append(f"""
        <div style="background: #131c2e; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 14px;">
                <div>
                    <span style="background:{sev_color};color:#fff;padding:4px 10px;border-radius:4px;font-weight:bold;font-size:12px;margin-right:8px;">{sev}</span>
                    <a href="https://semgrep.dev/r/{check_id}" target="_blank" style="font-family:monospace;font-size:15px;color:#38bdf8;text-decoration:none;font-weight:bold;">{check_id}</a>
                    <div style="margin-top:6px;font-size:13px;color:#94a3b8;">
                        📂 Tệp: <code>{path}:{line}</code> &nbsp;|&nbsp; 🏷️ Phân loại: <strong style="color:#f1f5f9;">{owasp}</strong> ({cwe})
                    </div>
                </div>
                <div style="font-size:12px;color:#64748b;font-family:monospace;">#{idx}</div>
            </div>

            <p style="color:#cbd5e1;font-size:14px;line-height:1.5;margin:0 0 16px 0;background:#0f172a;padding:12px;border-radius:6px;border-left:4px solid {sev_color};">
                <strong>Chi tiết:</strong> {msg}
            </p>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                <!-- SOURCE BOX -->
                <div style="background:#1e293b;border:1px solid #334155;border-radius:6px;padding:12px;">
                    <div style="display:flex;align-items:center;color:#facc15;font-size:13px;font-weight:bold;margin-bottom:8px;">
                        <span style="margin-right:6px;">🟡</span> SOURCE — Nguồn Dữ Liệu Ô Nhiễm (User Input)
                    </div>
                    <pre style="margin:0;background:#0b0f19;padding:10px;border-radius:4px;color:#fde047;font-family:monospace;font-size:12px;overflow-x:auto;white-space:pre-wrap;"><code>{src_lines_html}</code></pre>
                </div>

                <!-- SINK BOX -->
                <div style="background:#1e293b;border:1px solid #334155;border-radius:6px;padding:12px;">
                    <div style="display:flex;align-items:center;color:#f87171;font-size:13px;font-weight:bold;margin-bottom:8px;">
                        <span style="margin-right:6px;">🔴</span> SINK — Điểm Thực Thi Nguy Hiểm (Execution Sink)
                    </div>
                    <pre style="margin:0;background:#0b0f19;padding:10px;border-radius:4px;color:#fca5a5;font-family:monospace;font-size:12px;overflow-x:auto;white-space:pre-wrap;"><code>{snk_lines_html}</code></pre>
                </div>
            </div>
        </div>
        """)

    html_page = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Semgrep Security SAST Report - Source & Sink Analysis</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f8fafc; margin: 0; padding: 24px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 16px; margin-bottom: 24px; }}
        .badge {{ padding: 8px 16px; border-radius: 9999px; font-weight: bold; font-size: 14px; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #131c2e; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; }}
        .card-num {{ font-size: 28px; font-weight: bold; margin-top: 8px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1 style="margin:0 0 8px 0;font-size:24px;">🛡️ Báo Cáo Phân Tích Lỗ Hổng Bảo Mật (SOURCE & SINK)</h1>
            <p style="margin:0;color:#94a3b8;font-size:14px;">Bộ quy chuẩn chính thức từ Semgrep Community Registry: OWASP Top 10, CWE Top 25, PHP Security Audit</p>
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
            <div class="card-num" style="color:#f8fafc;">{len(findings)}</div>
        </div>
        <div class="card">
            <div style="color:#ef4444;font-size:13px;">NGHIÊM TRỌNG (ERROR)</div>
            <div class="card-num" style="color:#ef4444;">{len(errors)}</div>
        </div>
        <div class="card">
            <div style="color:#f59e0b;font-size:13px;">CẢNH BÁO (WARNING)</div>
            <div class="card-num" style="color:#f59e0b;">{len(warnings)}</div>
        </div>
    </div>

    <h2 style="font-size:18px;margin:24px 0 16px 0;">Danh Sách Lỗ Hổng & Dấu Vết Dòng Dữ Liệu (Source ➔ Sink)</h2>
    {''.join(cards_html)}
</div>
</body>
</html>
"""
    REPORT_HTML.write_text(html_page, encoding="utf-8")
    print(f"Generated Source-Sink Semgrep reports: {REPORT_HTML} and {REPORT_MD}")


if __name__ == "__main__":
    main()
