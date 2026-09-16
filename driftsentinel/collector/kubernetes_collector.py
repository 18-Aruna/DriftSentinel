"""Kubernetes live state collector.

Connects to the Kubernetes cluster via official Python client
and fetches live resources as Python dicts.
"""

from typing import List, Optional


class CollectorError(Exception):
    """Exception raised when Kubernetes cluster collection fails."""
    pass


class KubernetesCollector:
    """Collects live state from a Kubernetes cluster."""

    def __init__(self, kubeconfig_path: Optional[str] = None, context: Optional[str] = None):
        self.kubeconfig_path = kubeconfig_path
        self.context = context
        self._api_client = None

    def _init_client(self):
        """Lazy initialization of client."""
        if self._api_client is not None:
            return

        try:
            from kubernetes import config, client
            try:
                config.load_kube_config(
                    config_file=self.kubeconfig_path, context=self.context
                )
            except Exception:
                config.load_incluster_config()
            self._api_client = client.ApiClient()
            self._apps_v1 = client.AppsV1Api(self._api_client)
            self._core_v1 = client.CoreV1Api(self._api_client)
        except Exception as e:
            raise CollectorError(
                f"Failed to connect to Kubernetes cluster: {e}"
            )

    def collect(
        self, namespace: str = "default", resource_types: Optional[List[str]] = None
    ) -> List[dict]:
        """Fetch live resources as a list of resource dicts."""
        self._init_client()

        if resource_types is None:
            resource_types = ["Deployment", "Service", "ConfigMap"]

        live_resources: List[dict] = []

        if "Deployment" in resource_types:
            deps = self._apps_v1.list_namespaced_deployment(namespace=namespace)
            for item in deps.items:
                manifest = self._api_client.sanitize_for_serialization(item)
                manifest["kind"] = "Deployment"
                manifest["apiVersion"] = item.api_version or "apps/v1"
                if "metadata" in manifest and "namespace" not in manifest["metadata"]:
                    manifest["metadata"]["namespace"] = namespace
                live_resources.append(manifest)

        if "Service" in resource_types:
            svcs = self._core_v1.list_namespaced_service(namespace=namespace)
            for item in svcs.items:
                manifest = self._api_client.sanitize_for_serialization(item)
                manifest["kind"] = "Service"
                manifest["apiVersion"] = item.api_version or "v1"
                if "metadata" in manifest and "namespace" not in manifest["metadata"]:
                    manifest["metadata"]["namespace"] = namespace
                live_resources.append(manifest)

        if "ConfigMap" in resource_types:
            cms = self._core_v1.list_namespaced_config_map(namespace=namespace)
            for item in cms.items:
                manifest = self._api_client.sanitize_for_serialization(item)
                manifest["kind"] = "ConfigMap"
                manifest["apiVersion"] = item.api_version or "v1"
                if "metadata" in manifest and "namespace" not in manifest["metadata"]:
                    manifest["metadata"]["namespace"] = namespace
                live_resources.append(manifest)

        return live_resources
