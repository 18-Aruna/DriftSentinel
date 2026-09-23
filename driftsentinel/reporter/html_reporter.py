"""HTML reporter.

Generates a self-contained HTML report file with high-contrast text and styling.
"""

from datetime import datetime, timezone
import html
import os
from typing import List
from driftsentinel.models import DriftResult, HealResult, PolicyViolation


class HTMLReporter:
    """Generates standalone HTML report files for DriftSentinel runs."""

    @staticmethod
    def report(
        drifts: List[DriftResult],
        violations: List[PolicyViolation],
        heal_results: List[HealResult],
        output_path: str = "./reports/drift_report.html",
        scan_status: str = "COMPLETED",
        errors: List[str] = None,
    ) -> str:
        """Render HTML string and save to file. Returns output file path."""
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        html_content = HTMLReporter.render_html(
            drifts, violations, heal_results, timestamp, scan_status, errors
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    @staticmethod
    def render_html(
        drifts: List[DriftResult],
        violations: List[PolicyViolation],
        heal_results: List[HealResult],
        timestamp: str,
        scan_status: str = "COMPLETED",
        errors: List[str] = None,
    ) -> str:
        """Construct full HTML document string with high-contrast dark theme."""
        errors = errors or []
        total = len(drifts)
        drifted_count = sum(1 for d in drifts if d.drifted)
        in_sync_count = total - drifted_count
        unmanaged_count = sum(1 for d in drifts if d.extra_in_cluster)

        drift_rows = ""
        for res in drifts:
            status_text = res.status
            status_class = "badge-pass" if status_text == "IN_SYNC" else "badge-fail"

            diff_text = ""
            if res.diffs:
                diff_text = "<ul style='margin: 0; padding-left: 15px;'>"
                for d in res.diffs:
                    diff_text += f"<li><strong class='text-amber-300'>{html.escape(str(d.field_path))}</strong>: "
                    if d.desired_value is not None:
                        diff_text += f"Desired: <code>{html.escape(str(d.desired_value))}</code> "
                    if d.actual_value is not None:
                        diff_text += f"Actual: <code>{html.escape(str(d.actual_value))}</code>"
                    diff_text += "</li>"
                diff_text += "</ul>"
            else:
                diff_text = "<em>None</em>"

            drift_rows += f"""
            <tr class="hover:bg-slate-800/50">
                <td class="font-bold text-white">{html.escape(res.resource_kind)}/{html.escape(res.resource_name)}</td>
                <td class="text-slate-300">{html.escape(res.namespace)}</td>
                <td><span class="badge {status_class}">{status_text}</span></td>
                <td class="text-slate-200">{diff_text}</td>
            </tr>
            """

        policy_rows = ""
        for v in violations:
            sev_class = "badge-fail" if v.severity == "error" else "badge-warn"
            policy_rows += f"""
            <tr class="hover:bg-slate-800/50">
                <td class="font-bold text-white">{html.escape(v.policy_name)}</td>
                <td><span class="badge {sev_class}">{html.escape(v.severity.upper())}</span></td>
                <td class="text-slate-200">{html.escape(v.resource_kind)}/{html.escape(v.resource_name)}</td>
                <td class="text-slate-300">{html.escape(v.message)}</td>
            </tr>
            """

        if not policy_rows:
            policy_rows = "<tr><td colspan='4' class='text-slate-400'><em>No policy violations detected.</em></td></tr>"

        error_section = ""
        if errors:
            error_items = "".join(f"<li>{html.escape(error)}</li>" for error in errors)
            error_section = f"<div class='card'><h2>Execution Errors</h2><ul>{error_items}</ul></div>"

        heal_section = ""
        if heal_results:
            heal_section = "<div class='card'><h2>Auto-Healing Results</h2>"
            for h in heal_results:
                heal_class = "badge-pass" if h.success else "badge-fail"
                heal_section += f"""
                <p><strong class='text-slate-300'>Release:</strong> <span class='text-white font-bold'>{html.escape(h.release_name)}</span></p>
                <p><strong class='text-slate-300'>Action:</strong> <code>{html.escape(h.action)}</code></p>
                <p><strong class='text-slate-300'>Result:</strong> <span class="badge {heal_class}">{'SUCCESS' if h.success else 'FAILED'}</span></p>
                <p><strong class='text-slate-300'>Verified:</strong> <span class='text-white'>{h.verified}</span></p>
                <p><strong class='text-slate-300'>Details:</strong> <span class='text-slate-200'>{html.escape(h.message)}</span></p>
                <hr style='border-color: #334155; margin: 16px 0;'/>
                """
            heal_section += "</div>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DriftSentinel Report - {html.escape(timestamp)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #020617;
            color: #f8fafc;
            margin: 0;
            padding: 24px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header {{ background: #0f172a; color: #ffffff; padding: 24px; border-radius: 12px; border: 1px solid #1e293b; margin-bottom: 24px; }}
        .header h1 {{ margin: 0 0 8px 0; font-size: 28px; font-weight: 800; }}
        .header p {{ margin: 0; color: #94a3b8; font-size: 14px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: #0f172a; padding: 24px; border-radius: 12px; border: 1px solid #1e293b; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); margin-bottom: 24px; }}
        .card h2 {{ color: #ffffff; font-size: 18px; margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid #1e293b; padding-bottom: 12px; }}
        .metric-card {{ background: #0f172a; padding: 18px; border-radius: 12px; border: 1px solid #1e293b; text-align: center; }}
        .metric-card .title {{ font-size: 12px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
        .metric-card .number {{ font-size: 32px; font-weight: 800; margin-top: 6px; color: #ffffff; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #1e293b; font-size: 13px; }}
        th {{ background-color: #020617; color: #cbd5e1; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }}
        .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 0.03em; display: inline-block; }}
        .badge-pass {{ background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
        .badge-fail {{ background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
        .badge-warn {{ background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }}
        code {{ background: #020617; color: #e2e8f0; padding: 3px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #1e293b; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DriftSentinel Report</h1>
            <p>Generated at {html.escape(timestamp)} | Status: <strong>{html.escape(scan_status)}</strong></p>
        </div>

        <div class="summary-grid">
            <div class="metric-card"><div class="title">Total Scanned</div><div class="number">{total}</div></div>
            <div class="metric-card"><div class="title">In Sync</div><div class="number" style="color: #34d399;">{in_sync_count}</div></div>
            <div class="metric-card"><div class="title">Drifted</div><div class="number" style="color: #f87171;">{drifted_count}</div></div>
            <div class="metric-card"><div class="title">Unmanaged</div><div class="number" style="color: #fb923c;">{unmanaged_count}</div></div>
            <div class="metric-card"><div class="title">Policy Violations</div><div class="number" style="color: #fbbf24;">{len(violations)}</div></div>
        </div>

        <div class="card">
            <h2>Resource Drift Status</h2>
            <table>
                <thead>
                    <tr><th>Resource</th><th>Namespace</th><th>Status</th><th>Differences</th></tr>
                </thead>
                <tbody>{drift_rows}</tbody>
            </table>
        </div>

        <div class="card">
            <h2>Policy Compliance Rules</h2>
            <table>
                <thead>
                    <tr><th>Policy</th><th>Severity</th><th>Target Resource</th><th>Message</th></tr>
                </thead>
                <tbody>{policy_rows}</tbody>
            </table>
        </div>

        {error_section}
        {heal_section}
    </div>
</body>
</html>
"""


def report(
    drifts: List[DriftResult],
    violations: List[PolicyViolation],
    heal_results: List[HealResult],
    output_path: str = "./reports/drift_report.html",
    scan_status: str = "COMPLETED",
    errors: List[str] = None,
) -> str:
    """Module-level helper for HTML report."""
    return HTMLReporter.report(
        drifts, violations, heal_results, output_path, scan_status, errors
    )
