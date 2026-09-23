"""Configuration loader and validator for DriftSentinel.

Loads config.yaml, validates required fields, and provides
a typed configuration object to all other modules.
"""

from dataclasses import dataclass, field
import os
from typing import List, Optional
import yaml


class ConfigError(ValueError):
    """Raised when configuration cannot safely be used for a scan."""


@dataclass
class HelmConfig:
    chart_path: str = "./charts/sample-app"
    release_name: str = "sample-app"
    namespace: str = "default"
    values_file: Optional[str] = None


@dataclass
class KubernetesConfig:
    namespace: str = "default"
    resource_types: List[str] = field(
        default_factory=lambda: ["Deployment", "Service", "ConfigMap"]
    )


@dataclass
class PolicyConfig:
    enabled: bool = True
    file: str = "./policies/policies.yaml"


@dataclass
class AutoHealConfig:
    enabled: bool = False
    timeout: int = 60


@dataclass
class ReportingConfig:
    cli: bool = True
    html: bool = True
    html_output_dir: str = "./reports"


@dataclass
class Config:
    helm: HelmConfig = field(default_factory=HelmConfig)
    kubernetes: KubernetesConfig = field(default_factory=KubernetesConfig)
    policies: PolicyConfig = field(default_factory=PolicyConfig)
    auto_heal: AutoHealConfig = field(default_factory=AutoHealConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)


def load_config(config_path: str = "config.yaml") -> Config:
    """Load and parse configuration from a YAML file."""
    if not os.path.exists(config_path):
        return Config()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    helm_data = data.get("helm", {})
    helm_cfg = HelmConfig(
        chart_path=helm_data.get("chart_path", "./charts/sample-app"),
        release_name=helm_data.get("release_name", "sample-app"),
        namespace=helm_data.get("namespace", "default"),
        values_file=helm_data.get("values_file"),
    )

    k8s_data = data.get("kubernetes", {})
    k8s_cfg = KubernetesConfig(
        namespace=k8s_data.get("namespace", "default"),
        resource_types=k8s_data.get(
            "resource_types", ["Deployment", "Service", "ConfigMap"]
        ),
    )

    policy_data = data.get("policies", {})
    policy_cfg = PolicyConfig(
        enabled=policy_data.get("enabled", True),
        file=policy_data.get("file", "./policies/policies.yaml"),
    )

    heal_data = data.get("auto_heal", {})
    heal_cfg = AutoHealConfig(
        enabled=heal_data.get("enabled", False),
        timeout=heal_data.get("timeout", 60),
    )

    rep_data = data.get("reporting", {})
    rep_cfg = ReportingConfig(
        cli=rep_data.get("cli", True),
        html=rep_data.get("html", True),
        html_output_dir=rep_data.get("html_output_dir", "./reports"),
    )

    config = Config(
        helm=helm_cfg,
        kubernetes=k8s_cfg,
        policies=policy_cfg,
        auto_heal=heal_cfg,
        reporting=rep_cfg,
    )
    validate_config(config)
    return config


def validate_config(config: Config) -> None:
    """Validate settings that would otherwise produce misleading scan results."""
    if not config.helm.chart_path:
        raise ConfigError("helm.chart_path must be provided")
    if not os.path.isdir(config.helm.chart_path):
        raise ConfigError(f"Helm chart path does not exist: {config.helm.chart_path}")
    if config.helm.values_file and not os.path.isfile(config.helm.values_file):
        raise ConfigError(f"Values file does not exist: {config.helm.values_file}")
    if not config.helm.release_name or not config.helm.namespace:
        raise ConfigError("Helm release_name and namespace must be provided")
    if not config.kubernetes.namespace:
        raise ConfigError("kubernetes.namespace must be provided")
    if not config.kubernetes.resource_types or any(
        not isinstance(resource_type, str) or not resource_type
        for resource_type in config.kubernetes.resource_types
    ):
        raise ConfigError("kubernetes.resource_types must contain resource names")
    if config.auto_heal.timeout <= 0:
        raise ConfigError("auto_heal.timeout must be greater than zero")
    if config.policies.enabled and not os.path.isfile(config.policies.file):
        raise ConfigError(f"Policy file does not exist: {config.policies.file}")
