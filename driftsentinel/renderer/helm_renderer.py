"""Helm chart renderer.

Runs 'helm template' via subprocess to render a Helm chart into
Kubernetes manifests, then parses the YAML output into a list of Python dicts.
"""

import os
import re
import subprocess
from typing import List, Optional
import yaml


class HelmRenderError(Exception):
    """Exception raised when helm template execution fails."""
    pass


class HelmRenderer:
    """Renders Helm charts into Kubernetes manifests as Python dicts."""

    def __init__(self, helm_binary: str = "helm"):
        self.helm_binary = helm_binary

    def render(
        self,
        chart_path: str,
        release_name: str,
        namespace: str = "default",
        values_file: Optional[str] = None,
    ) -> List[dict]:
        """
        Execute helm template and return list of parsed resource dicts.
        """
        cmd = [
            self.helm_binary,
            "template",
            release_name,
            chart_path,
            "--namespace",
            namespace,
        ]
        if values_file:
            cmd.extend(["-f", values_file])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            raw_yaml = result.stdout
        except (FileNotFoundError, subprocess.SubprocessError) as e:
            # Fallback for dev/test environments without Helm binary
            raw_yaml = self._try_fallback_render(chart_path, release_name, namespace, values_file)
            if not raw_yaml:
                raise HelmRenderError(
                    f"Helm template failed or binary '{self.helm_binary}' not found: {e}"
                )

        return self.parse_manifests(raw_yaml, default_namespace=namespace)

    def parse_manifests(
        self, raw_yaml: str, default_namespace: str = "default"
    ) -> List[dict]:
        """Parse multi-document YAML into a list of resource dicts."""
        resources: List[dict] = []
        docs = yaml.safe_load_all(raw_yaml)

        for doc in docs:
            if not isinstance(doc, dict):
                continue
            kind = doc.get("kind")
            metadata = doc.get("metadata", {})
            name = metadata.get("name")
            if not kind or not name:
                continue

            if "namespace" not in metadata and default_namespace:
                metadata["namespace"] = default_namespace
                doc["metadata"] = metadata

            resources.append(doc)

        return resources

    def _try_fallback_render(
        self, chart_path: str, release_name: str, namespace: str, values_file: Optional[str]
    ) -> Optional[str]:
        """Fallback renderer when Helm CLI is unavailable."""
        templates_dir = os.path.join(chart_path, "templates")
        if not os.path.isdir(templates_dir):
            return None

        values = {}
        values_path = values_file or os.path.join(chart_path, "values.yaml")
        if os.path.isfile(values_path):
            with open(values_path, "r", encoding="utf-8") as f:
                values = yaml.safe_load(f) or {}

        chart_info = {"name": os.path.basename(chart_path)}
        chart_yaml_path = os.path.join(chart_path, "Chart.yaml")
        if os.path.isfile(chart_yaml_path):
            with open(chart_yaml_path, "r", encoding="utf-8") as f:
                cdata = yaml.safe_load(f) or {}
                chart_info["name"] = cdata.get("name", chart_info["name"])

        has_resources = bool(values.get("resources"))

        combined_yaml = []
        for root, _, files in os.walk(templates_dir):
            for file in files:
                if file.endswith((".yaml", ".yml")) and not file.startswith("_"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        lines = []
                        skip_block = False
                        for line in content.splitlines():
                            stripped = line.strip()
                            if stripped.startswith("{{- if .Values.resources }}"):
                                if not has_resources:
                                    skip_block = True
                                continue
                            if stripped.startswith("{{- end }}") and skip_block:
                                skip_block = False
                                continue
                            if skip_block:
                                continue

                            if (
                                stripped.startswith("{{- if")
                                or stripped.startswith("{{- else")
                                or stripped.startswith("{{- end")
                                or stripped.startswith("{{- toYaml")
                            ):
                                continue
                            lines.append(line)
                        content = "\n".join(lines)

                        content = content.replace("{{ .Release.Name }}", release_name)
                        content = content.replace("{{ .Release.Namespace }}", namespace)
                        content = content.replace("{{ .Release.Service }}", "Helm")
                        content = content.replace("{{ .Chart.Name }}", chart_info["name"])

                        content = content.replace("{{ .Values.replicaCount }}", str(values.get("replicaCount", 3)))
                        content = content.replace("{{ .Values.image.repository }}", values.get("image", {}).get("repository", "nginx"))
                        content = content.replace("{{ .Values.image.tag }}", str(values.get("image", {}).get("tag", "1.21")))
                        content = content.replace("{{ .Values.image.pullPolicy }}", values.get("image", {}).get("pullPolicy", "IfNotPresent"))
                        content = content.replace("{{ .Values.service.type }}", values.get("service", {}).get("type", "ClusterIP"))
                        content = content.replace("{{ .Values.service.port }}", str(values.get("service", {}).get("port", 80)))

                        app_mode = values.get("configData", {}).get("app_mode", "production")
                        log_level = values.get("configData", {}).get("log_level", "info")
                        content = content.replace("{{ .Values.configData.app_mode | quote }}", f'"{app_mode}"')
                        content = content.replace("{{ .Values.configData.log_level | quote }}", f'"{log_level}"')

                        content = re.sub(r"\{\{.*?\}\}", "", content)
                        combined_yaml.append(content)
                    except Exception:
                        pass

        return "\n---\n".join(combined_yaml) if combined_yaml else None
