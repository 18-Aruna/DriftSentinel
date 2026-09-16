"""DriftSentinel main entry point and orchestrator.

Executes the pipeline: render → collect → normalize → detect → policy → heal → report.
"""

import os
import sys
from typing import List, Optional
import yaml

from driftsentinel.config import load_config
from driftsentinel.collector.kubernetes_collector import KubernetesCollector
from driftsentinel.detector.drift_detector import detect_drift
from driftsentinel.healer.auto_healer import heal
from driftsentinel.models import DriftResult, HealResult, PolicyViolation
from driftsentinel.policy.policy_engine import evaluate
from driftsentinel.renderer.helm_renderer import HelmRenderer
from driftsentinel.reporter.cli_reporter import report as cli_report
from driftsentinel.reporter.html_reporter import report as html_report


def run_pipeline(config_path: str = "config.yaml") -> int:
    """Execute full DriftSentinel pipeline."""
    config = load_config(config_path)

    # 1. Render Desired State
    renderer = HelmRenderer()
    desired_resources: List[dict] = []
    try:
        desired_resources = renderer.render(
            chart_path=config.helm.chart_path,
            release_name=config.helm.release_name,
            namespace=config.helm.namespace,
            values_file=config.helm.values_file,
        )
    except Exception as e:
        print(f"[WARNING] Desired state rendering warning: {e}", file=sys.stderr)

    # 2. Collect Live State
    collector = KubernetesCollector()
    live_resources: List[dict] = []
    try:
        live_resources = collector.collect(
            namespace=config.kubernetes.namespace,
            resource_types=config.kubernetes.resource_types,
        )
    except Exception as e:
        print(f"[WARNING] Live cluster collection warning: {e}", file=sys.stderr)

    # 3. Detect Drift
    drifts: List[DriftResult] = detect_drift(desired_resources, live_resources)

    # 4. Evaluate Policy Rules
    violations: List[PolicyViolation] = []
    if config.policies.enabled and os.path.exists(config.policies.file):
        with open(config.policies.file, "r", encoding="utf-8") as f:
            pdata = yaml.safe_load(f) or {}
            policies_list = pdata.get("policies", [])
            violations = evaluate(live_resources, policies_list)

    # 5. Auto-Healing
    heal_results: List[HealResult] = []
    has_drift = any(d.drifted for d in drifts)
    if config.auto_heal.enabled and has_drift:
        heal_res = heal(
            release_name=config.helm.release_name,
            chart_path=config.helm.chart_path,
            namespace=config.helm.namespace,
            values_file=config.helm.values_file,
        )

        # Verification: re-collect live state and re-detect drift
        try:
            recollected_live = collector.collect(
                namespace=config.kubernetes.namespace,
                resource_types=config.kubernetes.resource_types,
            )
            remaining = detect_drift(desired_resources, recollected_live)
            heal_res.remaining_drifts = remaining
            heal_res.verified = not any(r.drifted for r in remaining)
        except Exception:
            heal_res.verified = False

        heal_results.append(heal_res)

    # 6. Reporting
    if config.reporting.cli:
        cli_report(drifts, violations, heal_results)

    if config.reporting.html:
        out_path = os.path.join(config.reporting.html_output_dir, "drift_report_latest.html")
        generated_file = html_report(drifts, violations, heal_results, output_path=out_path)
        print(f"[INFO] HTML report generated: {generated_file}")

    # Return exit code: 0 = no drift, 1 = drift detected
    if any(d.drifted for d in drifts):
        return 1
    return 0


def main():
    """CLI execution entrypoint."""
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    try:
        exit_code = run_pipeline(config_path=config_path)
        sys.exit(exit_code)
    except Exception as e:
        print(f"[ERROR] DriftSentinel execution failed: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
