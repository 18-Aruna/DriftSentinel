"""Data models for DriftSentinel matching the Architecture & Design Document."""

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class FieldDiff:
    """Field-level difference between desired and live resources."""
    field_path: str
    desired_value: Any
    actual_value: Any


@dataclass
class DriftResult:
    """Drift evaluation result for a single resource."""
    resource_kind: str
    resource_name: str
    namespace: str
    drifted: bool
    missing_in_cluster: bool
    diffs: List[FieldDiff] = field(default_factory=list)
    extra_in_cluster: bool = False

    @property
    def status(self) -> str:
        """Return a stable status label for reports and integrations."""
        if self.missing_in_cluster:
            return "MISSING"
        if self.extra_in_cluster:
            return "UNMANAGED"
        return "DRIFTED" if self.drifted else "IN_SYNC"


@dataclass
class PolicyViolation:
    """A compliance policy rule violation."""
    resource_kind: str
    resource_name: str
    namespace: str
    policy_name: str
    message: str
    severity: str  # "warning" or "error"


@dataclass
class HealResult:
    """Result of an auto-healing attempt."""
    release_name: str
    action: str  # e.g., "helm upgrade --install"
    success: bool
    message: str
    verified: bool  # Did post-heal drift check pass?
    remaining_drifts: List[DriftResult] = field(default_factory=list)
    timestamp: str = ""
