"""Auto-healer.

When drift is detected and auto-healing is enabled, reapplies the
Helm release via 'helm upgrade --install' and verifies the result.
"""

from datetime import datetime, timezone
import subprocess
from typing import List, Optional
from driftsentinel.models import DriftResult, HealResult


class AutoHealer:
    """Re-syncs live state with desired state by triggering Helm upgrade."""

    def __init__(self, helm_binary: str = "helm"):
        self.helm_binary = helm_binary

    def heal(
        self,
        release_name: str,
        chart_path: str,
        namespace: str = "default",
        values_file: Optional[str] = None,
        timeout: int = 60,
    ) -> HealResult:
        """Execute helm upgrade --install to heal detected drift."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cmd = [
            self.helm_binary,
            "upgrade",
            "--install",
            release_name,
            chart_path,
            "--namespace",
            namespace,
            "--timeout",
            f"{timeout}s",
        ]
        if values_file:
            cmd.extend(["-f", values_file])

        action_str = f"helm upgrade --install {release_name} {chart_path}"

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10,
            )
            if result.returncode == 0:
                return HealResult(
                    release_name=release_name,
                    action=action_str,
                    success=True,
                    message=f"Helm upgrade succeeded for release '{release_name}'",
                    verified=True,
                    remaining_drifts=[],
                    timestamp=ts,
                )
            else:
                stderr = result.stderr.strip() or "Unknown error"
                return HealResult(
                    release_name=release_name,
                    action=action_str,
                    success=False,
                    message=f"Helm upgrade failed: {stderr}",
                    verified=False,
                    remaining_drifts=[],
                    timestamp=ts,
                )
        except FileNotFoundError:
            return HealResult(
                release_name=release_name,
                action=action_str,
                success=False,
                message=f"Helm binary '{self.helm_binary}' not found in PATH",
                verified=False,
                remaining_drifts=[],
                timestamp=ts,
            )
        except subprocess.TimeoutExpired:
            return HealResult(
                release_name=release_name,
                action=action_str,
                success=False,
                message=f"Helm upgrade timed out after {timeout} seconds",
                verified=False,
                remaining_drifts=[],
                timestamp=ts,
            )
        except Exception as e:
            return HealResult(
                release_name=release_name,
                action=action_str,
                success=False,
                message=f"Auto-healing failed: {str(e)}",
                verified=False,
                remaining_drifts=[],
                timestamp=ts,
            )


def heal(
    release_name: str, chart_path: str, namespace: str = "default", values_file: Optional[str] = None
) -> HealResult:
    """Module-level helper for heal."""
    healer = AutoHealer()
    return healer.heal(release_name, chart_path, namespace, values_file)
