"""Unit tests for reporters."""

import os
import tempfile
from driftsentinel.models import DriftResult, FieldDiff, PolicyViolation
from driftsentinel.reporter.cli_reporter import report as cli_report
from driftsentinel.reporter.html_reporter import report as html_report


def test_cli_reporter(capsys):
    diff = FieldDiff(field_path="spec.replicas", desired_value=2, actual_value=5)
    res = DriftResult("Deployment", "sample-app-nginx", "default", drifted=True, missing_in_cluster=False, diffs=[diff])
    violation = PolicyViolation("Deployment", "sample-app-nginx", "default", "no-latest-tag", "Found latest tag", "error")

    cli_report([res], [violation], [])
    captured = capsys.readouterr()
    assert "DRIFTSENTINEL EXECUTION REPORT" in captured.out
    assert "Deployment/sample-app-nginx" in captured.out
    assert "no-latest-tag" in captured.out


def test_html_reporter():
    diff = FieldDiff(field_path="spec.replicas", desired_value=2, actual_value=5)
    res = DriftResult("Deployment", "sample-app-nginx", "default", drifted=True, missing_in_cluster=False, diffs=[diff])

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = os.path.join(tmp_dir, "test_report.html")
        generated = html_report([res], [], [], output_path=out_file)
        assert os.path.isfile(generated)
        with open(generated, "r", encoding="utf-8") as f:
            html_text = f.read()
            assert "DriftSentinel Report" in html_text
            assert "sample-app-nginx" in html_text
