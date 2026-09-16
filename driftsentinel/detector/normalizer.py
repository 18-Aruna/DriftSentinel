"""Kubernetes resource normalizer.

Strips Kubernetes-injected runtime fields (uid, resourceVersion, managedFields,
status, etc.) and sorts collection lists for deterministic comparisons.
"""

import copy
from typing import Any, Dict


FIELDS_TO_REMOVE_METADATA = [
    "uid",
    "resourceVersion",
    "generation",
    "creationTimestamp",
    "managedFields",
    "selfLink",
    "finalizers",
    "ownerReferences",
    "deletionTimestamp",
]

ANNOTATIONS_TO_REMOVE = [
    "kubectl.kubernetes.io/last-applied-configuration",
    "deployment.kubernetes.io/revision",
]


class ResourceNormalizer:
    """Normalizes Kubernetes resource dictionaries."""

    @staticmethod
    def normalize(resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a cleaned deep copy of a Kubernetes resource dict.
        Pure function with no side effects.
        """
        if not resource or not isinstance(resource, dict):
            return {}

        clean = copy.deepcopy(resource)

        # 1. Remove status block
        clean.pop("status", None)

        # 2. Secret safety: Strip data from Secret resources
        kind = clean.get("kind")
        if kind == "Secret":
            clean.pop("data", None)
            clean.pop("stringData", None)

        # 3. Clean metadata fields
        metadata = clean.get("metadata")
        if isinstance(metadata, dict):
            for m_field in FIELDS_TO_REMOVE_METADATA:
                metadata.pop(m_field, None)

            annotations = metadata.get("annotations")
            if isinstance(annotations, dict):
                for anno in ANNOTATIONS_TO_REMOVE:
                    annotations.pop(anno, None)
                if not annotations:
                    metadata.pop("annotations", None)

        # 4. Clean Deployment specs & sort container lists / env vars
        if kind == "Deployment":
            spec = clean.get("spec")
            if isinstance(spec, dict):
                spec.pop("revisionHistoryLimit", None)
                spec.pop("progressDeadlineSeconds", None)
                pod_spec = spec.get("template", {}).get("spec")
                if isinstance(pod_spec, dict):
                    pod_spec.pop("schedulerName", None)
                    pod_spec.pop("dnsPolicy", None)
                    pod_spec.pop("restartPolicy", None)
                    pod_spec.pop("terminationGracePeriodSeconds", None)

                    containers = pod_spec.get("containers")
                    if isinstance(containers, list):
                        # Sort containers by name
                        containers.sort(key=lambda c: c.get("name", ""))
                        for c in containers:
                            # Sort env vars by name
                            env = c.get("env")
                            if isinstance(env, list):
                                env.sort(key=lambda e: e.get("name", ""))
                            # Sort ports by containerPort
                            ports = c.get("ports")
                            if isinstance(ports, list):
                                ports.sort(key=lambda p: p.get("containerPort", 0))

        # 5. Clean Service defaults
        elif kind == "Service":
            spec = clean.get("spec")
            if isinstance(spec, dict):
                spec.pop("clusterIP", None)
                spec.pop("clusterIPs", None)
                spec.pop("internalTrafficPolicy", None)
                spec.pop("ipFamilies", None)
                spec.pop("ipFamilyPolicy", None)
                spec.pop("sessionAffinity", None)

        return clean


def normalize(resource: dict) -> dict:
    """Module-level helper for normalize."""
    return ResourceNormalizer.normalize(resource)
