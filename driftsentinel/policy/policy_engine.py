"""Policy engine.

Evaluates live Kubernetes resources against YAML-defined compliance policies.
"""

from typing import Any, Dict, List, Tuple
from driftsentinel.models import PolicyViolation


class PolicyEngine:
    """Evaluates live resources against policy rules."""

    def evaluate(
        self, live_resources: List[dict], policies: List[dict]
    ) -> List[PolicyViolation]:
        """
        Evaluate live resource dicts against a list of policy dicts.
        """
        violations: List[PolicyViolation] = []

        for policy in policies:
            name = policy.get("name", "unnamed-policy")
            description = policy.get("description", "")
            severity = policy.get("severity", "warning")
            target_kinds = policy.get("resource_types", [])
            rule = policy.get("rule", {})

            path = rule.get("path", "")
            operator = rule.get("operator", "exists")
            expected_value = rule.get("value")

            for manifest in live_resources:
                if not isinstance(manifest, dict):
                    continue
                kind = manifest.get("kind", "")
                metadata = manifest.get("metadata", {})
                name_res = metadata.get("name", "")
                namespace = metadata.get("namespace", "default")

                if target_kinds and kind not in target_kinds:
                    continue

                is_valid, msg = self._evaluate_rule(manifest, path, operator, expected_value)
                if not is_valid:
                    violations.append(
                        PolicyViolation(
                            resource_kind=kind,
                            resource_name=name_res,
                            namespace=namespace,
                            policy_name=name,
                            message=msg or f"Rule '{operator}' failed on path '{path}'",
                            severity=severity,
                        )
                    )

        return violations

    def _evaluate_rule(
        self, manifest: dict, path: str, operator: str, expected_value: Any
    ) -> Tuple[bool, str]:
        """Evaluate a single rule with [*] wildcard path resolution."""
        extracted_values = self._extract_path_values(manifest, path)

        if not extracted_values:
            if operator == "not_exists":
                return True, ""
            return False, f"Field path '{path}' does not exist"

        for val in extracted_values:
            valid, msg = self._check_operator(val, operator, expected_value)
            if not valid:
                return False, msg

        return True, ""

    def _check_operator(
        self, val: Any, operator: str, expected_value: Any
    ) -> Tuple[bool, str]:
        """Check operator condition on a single value."""
        if operator == "exists":
            if val is None:
                return False, "Value is None"
            return True, ""

        elif operator == "not_exists":
            if val is not None:
                return False, f"Value exists: {val}"
            return True, ""

        elif operator == "equals":
            if val != expected_value:
                return False, f"Expected '{expected_value}', got '{val}'"
            return True, ""

        elif operator == "not_equals":
            if val == expected_value:
                return False, f"Value equals '{expected_value}'"
            return True, ""

        elif operator == "contains":
            if isinstance(val, (str, list, dict)):
                if expected_value not in val:
                    return False, f"'{val}' does not contain '{expected_value}'"
                return True, ""
            return False, f"Cannot evaluate 'contains' on type {type(val).__name__}"

        elif operator == "not_contains":
            if isinstance(val, (str, list, dict)):
                if expected_value in val:
                    return False, f"'{val}' contains prohibited substring '{expected_value}'"
                return True, ""
            return False, f"Cannot evaluate 'not_contains' on type {type(val).__name__}"

        elif operator == "gte":
            try:
                if float(val) < float(expected_value):
                    return False, f"Value {val} is less than required {expected_value}"
                return True, ""
            except (ValueError, TypeError):
                return False, f"Value {val} is not numeric"

        elif operator == "lte":
            try:
                if float(val) > float(expected_value):
                    return False, f"Value {val} is greater than required {expected_value}"
                return True, ""
            except (ValueError, TypeError):
                return False, f"Value {val} is not numeric"

        return False, f"Unknown operator '{operator}'"

    def _extract_path_values(self, data: Any, path: str) -> List[Any]:
        """Extract values supporting [*] array wildcard."""
        if not path or data is None:
            return []

        parts = path.split(".")
        current_nodes = [data]

        for part in parts:
            next_nodes = []
            if part.endswith("[*]"):
                key = part[:-3]
                for node in current_nodes:
                    if isinstance(node, dict) and key in node:
                        items = node[key]
                        if isinstance(items, list):
                            next_nodes.extend(items)
            else:
                for node in current_nodes:
                    if isinstance(node, dict) and part in node:
                        next_nodes.append(node[part])
            current_nodes = next_nodes
            if not current_nodes:
                break

        return current_nodes


def evaluate(live_resources: List[dict], policies: List[dict]) -> List[PolicyViolation]:
    """Module-level helper for evaluate."""
    engine = PolicyEngine()
    return engine.evaluate(live_resources, policies)
