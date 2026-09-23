"""CLI reporter.

Prints drift results, policy violations, and healing results
to stdout in terminal format.
"""

from typing import List
from driftsentinel.models import DriftResult, HealResult, PolicyViolation


class CLIReporter:
    """Prints DriftSentinel execution summary to the CLI."""

    @staticmethod
    def report(
        drifts: List[DriftResult],
        violations: List[PolicyViolation],
        heal_results: List[HealResult],
        scan_status: str = "COMPLETED",
        errors: List[str] = None,
    ) -> None:
        """Print formatted terminal report."""
        errors = errors or []
        print()
        print("==========================================================================")
        print("                       DRIFTSENTINEL EXECUTION REPORT                      ")
        print("==========================================================================")
        print(f"Scan Status              : {scan_status}")
        if errors:
            print("Execution Errors         :")
            for error in errors:
                print(f"  - {error}")
        print()
        print()

        total = len(drifts)
        drifted_count = sum(1 for d in drifts if d.drifted)
        in_sync_count = total - drifted_count
        missing_count = sum(1 for d in drifts if d.missing_in_cluster)
        unmanaged_count = sum(1 for d in drifts if d.extra_in_cluster)

        # 1. Resource Drift Summary
        print("--- Resource Drift Summary ---")
        print(f"Total Resources Scanned : {total}")
        print(f"In Sync                 : {in_sync_count}")
        print(f"Drifted                 : {drifted_count}")
        print(f"Missing in Cluster      : {missing_count}")
        print(f"Unmanaged in Cluster    : {unmanaged_count}")
        print()

        # 2. Detailed Drift Breakdown
        if drifts:
            print("--- Resource Details ---")
            header = f"{'RESOURCE':<40} | {'STATUS':<15} | {'DIFF COUNT'}"
            print(header)
            print("-" * len(header))
            for res in drifts:
                name_str = f"{res.resource_kind}/{res.resource_name}"
                status = res.status
                diff_count = len(res.diffs)
                print(f"{name_str:<40} | {status:<15} | {diff_count}")
                for diff in res.diffs:
                    print(f"    |- Path: {diff.field_path}")
                    if diff.desired_value is not None:
                        print(f"    |   Desired: {diff.desired_value}")
                    if diff.actual_value is not None:
                        print(f"    |   Actual : {diff.actual_value}")
            print()

        # 3. Policy Compliance Summary
        print("--- Policy Compliance Summary ---")
        print(f"Violations      : {len(violations)}")
        print()

        if violations:
            print("--- Policy Violations ---")
            p_header = f"{'POLICY NAME':<25} | {'SEVERITY':<10} | {'RESOURCE':<30} | {'MESSAGE'}"
            print(p_header)
            print("-" * 90)
            for v in violations:
                res_str = f"{v.resource_kind}/{v.resource_name}"
                print(f"{v.policy_name:<25} | {v.severity.upper():<10} | {res_str:<30} | {v.message}")
            print()

        # 4. Auto-Heal Status
        if heal_results:
            print("--- Auto-Healing Status ---")
            for h in heal_results:
                status = "SUCCESS" if h.success else "FAILED"
                print(f"Release   : {h.release_name}")
                print(f"Action    : {h.action}")
                print(f"Result    : {status}")
                print(f"Verified  : {h.verified}")
                print(f"Message   : {h.message}")
                print()

        print("==========================================================================")
        print()


def report(
    drifts: List[DriftResult],
    violations: List[PolicyViolation],
    heal_results: List[HealResult],
    scan_status: str = "COMPLETED",
    errors: List[str] = None,
) -> None:
    """Module-level helper for CLI report."""
    CLIReporter.report(drifts, violations, heal_results, scan_status, errors)
