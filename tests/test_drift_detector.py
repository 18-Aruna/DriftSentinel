"""Unit tests for DriftDetector."""

from driftsentinel.detector.drift_detector import detect_drift


def test_drift_detector_in_sync():
    desired = [{"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "app", "namespace": "default"}, "spec": {"replicas": 2}}]
    live = [{"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "app", "namespace": "default", "uid": "xyz"}, "spec": {"replicas": 2}, "status": {"ready": 2}}]

    results = detect_drift(desired, live)

    assert len(results) == 1
    assert not results[0].drifted
    assert not results[0].missing_in_cluster
    assert len(results[0].diffs) == 0


def test_drift_detector_field_modified():
    desired = [{"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "app", "namespace": "default"}, "spec": {"replicas": 2}}]
    live = [{"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "app", "namespace": "default"}, "spec": {"replicas": 5}}]

    results = detect_drift(desired, live)

    assert len(results) == 1
    assert results[0].drifted
    assert not results[0].missing_in_cluster
    assert len(results[0].diffs) == 1
    assert results[0].diffs[0].desired_value == 2
    assert results[0].diffs[0].actual_value == 5


def test_drift_detector_missing_in_cluster():
    desired = [{"apiVersion": "v1", "kind": "Service", "metadata": {"name": "svc", "namespace": "default"}}]
    live = []

    results = detect_drift(desired, live)

    assert len(results) == 1
    assert results[0].drifted
    assert results[0].missing_in_cluster
