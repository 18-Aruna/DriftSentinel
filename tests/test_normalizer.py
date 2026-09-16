"""Unit tests for ResourceNormalizer."""

from driftsentinel.detector.normalizer import ResourceNormalizer, normalize


def test_normalizer_strips_status_and_metadata():
    raw_manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "sample-app",
            "namespace": "default",
            "uid": "12345-abcde",
            "resourceVersion": "999",
            "generation": 2,
            "managedFields": [{"manager": "kubectl"}],
            "annotations": {
                "kubectl.kubernetes.io/last-applied-configuration": "{}"
            }
        },
        "spec": {
            "replicas": 3
        },
        "status": {
            "availableReplicas": 3
        }
    }

    cleaned = normalize(raw_manifest)

    assert "status" not in cleaned
    assert cleaned["metadata"]["name"] == "sample-app"
    assert "uid" not in cleaned["metadata"]
    assert "resourceVersion" not in cleaned["metadata"]
    assert "managedFields" not in cleaned["metadata"]
    assert "annotations" not in cleaned["metadata"]
    assert cleaned["spec"]["replicas"] == 3


def test_normalizer_strips_secret_data():
    raw_secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": "db-secret"},
        "data": {"password": "c2VjcmV0cGFzc3dvcmQ="}
    }

    cleaned = normalize(raw_secret)
    assert "data" not in cleaned
    assert cleaned["metadata"]["name"] == "db-secret"
