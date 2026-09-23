"""Pipeline exit-code regression tests."""

from driftsentinel.config import Config
from driftsentinel.main import run_pipeline


def test_pipeline_returns_error_when_collection_fails(monkeypatch):
    config = Config()
    config.reporting.cli = False
    config.reporting.html = False

    class Renderer:
        def render(self, **kwargs):
            return []

    class Collector:
        def collect(self, **kwargs):
            raise RuntimeError("cluster unavailable")

    monkeypatch.setattr("driftsentinel.main.load_config", lambda _: config)
    monkeypatch.setattr("driftsentinel.main.HelmRenderer", Renderer)
    monkeypatch.setattr("driftsentinel.main.KubernetesCollector", Collector)

    assert run_pipeline("ignored.yaml") == 2


def test_pipeline_returns_policy_failure_code(monkeypatch):
    config = Config()
    config.policies.enabled = True
    config.policies.file = "policies/policies.yaml"
    config.reporting.cli = False
    config.reporting.html = False

    desired = [{"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "app", "namespace": "default"}, "spec": {"replicas": 1}}]

    class Renderer:
        def render(self, **kwargs):
            return desired

    class Collector:
        def collect(self, **kwargs):
            return desired

    monkeypatch.setattr("driftsentinel.main.load_config", lambda _: config)
    monkeypatch.setattr("driftsentinel.main.HelmRenderer", Renderer)
    monkeypatch.setattr("driftsentinel.main.KubernetesCollector", Collector)

    assert run_pipeline("ignored.yaml") == 3