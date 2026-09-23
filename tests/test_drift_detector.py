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


def test_drift_detector_reports_unmanaged_live_resource():
    live = [{"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "manual", "namespace": "default"}}]

    results = detect_drift([], live)

    assert len(results) == 1
    assert results[0].drifted
    assert results[0].extra_in_cluster
    assert results[0].status == "UNMANAGED"


def test_drift_detector_reports_live_only_fields():
    desired = [{"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "config", "namespace": "default"}, "data": {"mode": "safe"}}]
    live = [{"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "config", "namespace": "default"}, "data": {"mode": "safe", "extra": "value"}}]

    results = detect_drift(desired, live)

    assert results[0].drifted
    assert any(diff.field_path == "['data']['extra']" for diff in results[0].diffs)
