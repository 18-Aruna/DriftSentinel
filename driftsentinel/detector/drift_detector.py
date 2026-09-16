"""Drift detector.

Compares normalized desired state against normalized live state
and produces structured DriftResult objects with FieldDiff details.
"""

from typing import Dict, List, Tuple
from deepdiff import DeepDiff

from driftsentinel.detector.normalizer import ResourceNormalizer
from driftsentinel.models import DriftResult, FieldDiff


class DriftDetector:
    """Detects configuration drift between desired and live Kubernetes resources."""

    def __init__(self, normalizer: ResourceNormalizer = None):
        self.normalizer = normalizer or ResourceNormalizer()

    def detect_drift(
        self, desired: List[dict], live: List[dict]
    ) -> List[DriftResult]:
        """
        Compare list of desired resource dicts against list of live resource dicts.
        """
        results: List[DriftResult] = []

        def get_key(res: dict) -> Tuple[str, str, str, str]:
            meta = res.get("metadata", {})
            return (
                res.get("apiVersion", ""),
                res.get("kind", ""),
                meta.get("namespace", "default"),
                meta.get("name", ""),
            )

        desired_map: Dict[Tuple[str, str, str, str], dict] = {
            get_key(r): r for r in desired if isinstance(r, dict) and get_key(r)[3]
        }
        live_map: Dict[Tuple[str, str, str, str], dict] = {
            get_key(r): r for r in live if isinstance(r, dict) and get_key(r)[3]
        }

        all_keys = set(desired_map.keys()).union(set(live_map.keys()))

        for key in sorted(all_keys, key=lambda k: (k[1], k[3], k[2])):
            api_version, kind, namespace, name = key
            desired_manifest = desired_map.get(key)
            live_manifest = live_map.get(key)

            if desired_manifest and not live_manifest:
                results.append(
                    DriftResult(
                        resource_kind=kind,
                        resource_name=name,
                        namespace=namespace,
                        drifted=True,
                        missing_in_cluster=True,
                        diffs=[
                            FieldDiff(
                                field_path="root",
                                desired_value="Resource defined in Helm chart",
                                actual_value="Not found in cluster",
                            )
                        ],
                    )
                )

            elif live_manifest and not desired_manifest:
                # Extra in cluster (untracked, skipped or reported)
                continue

            else:
                norm_desired = self.normalizer.normalize(desired_manifest)
                norm_live = self.normalizer.normalize(live_manifest)

                diffs = self._compute_diffs(norm_desired, norm_live)
                drifted = len(diffs) > 0

                results.append(
                    DriftResult(
                        resource_kind=kind,
                        resource_name=name,
                        namespace=namespace,
                        drifted=drifted,
                        missing_in_cluster=False,
                        diffs=diffs,
                    )
                )

        return results

    def _compute_diffs(self, desired: dict, live: dict) -> List[FieldDiff]:
        """Left-side aware field diff using DeepDiff."""
        ddiff = DeepDiff(desired, live, ignore_order=True)
        diff_list: List[FieldDiff] = []

        if "values_changed" in ddiff:
            for path, change in ddiff["values_changed"].items():
                clean_path = path.replace("root", "")
                diff_list.append(
                    FieldDiff(
                        field_path=clean_path,
                        desired_value=change["old_value"],
                        actual_value=change["new_value"],
                    )
                )

        if "dictionary_item_removed" in ddiff:
            for item in ddiff["dictionary_item_removed"]:
                clean_path = str(item).replace("root", "")
                diff_list.append(
                    FieldDiff(
                        field_path=clean_path,
                        desired_value="[Present in Helm chart]",
                        actual_value=None,
                    )
                )

        if "type_changes" in ddiff:
            for path, change in ddiff["type_changes"].items():
                clean_path = path.replace("root", "")
                diff_list.append(
                    FieldDiff(
                        field_path=clean_path,
                        desired_value=change["old_value"],
                        actual_value=change["new_value"],
                    )
                )

        return diff_list


def detect_drift(desired: List[dict], live: List[dict]) -> List[DriftResult]:
    """Module-level function for detect_drift."""
    detector = DriftDetector()
    return detector.detect_drift(desired, live)
