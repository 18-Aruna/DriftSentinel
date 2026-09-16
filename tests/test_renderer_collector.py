"""Unit tests for HelmRenderer parsing."""

from driftsentinel.renderer.helm_renderer import HelmRenderer


def test_helm_renderer_parse_manifests():
    raw_yaml = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app-nginx
  namespace: default
spec:
  replicas: 2
---
apiVersion: v1
kind: Service
metadata:
  name: sample-app-svc
  namespace: default
spec:
  ports:
    - port: 80
"""

    renderer = HelmRenderer()
    resources = renderer.parse_manifests(raw_yaml)

    assert isinstance(resources, list)
    assert len(resources) == 2
    assert resources[0]["kind"] == "Deployment"
    assert resources[0]["metadata"]["name"] == "sample-app-nginx"
    assert resources[1]["kind"] == "Service"
    assert resources[1]["metadata"]["name"] == "sample-app-svc"
