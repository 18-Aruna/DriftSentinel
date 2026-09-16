"""Unit tests for PolicyEngine."""

from driftsentinel.policy.policy_engine import evaluate


def test_policy_engine_operators():
    policies = [
        {
            "name": "replica-count-policy",
            "severity": "warning",
            "resource_types": ["Deployment"],
            "rule": {
                "path": "spec.replicas",
                "operator": "gte",
                "value": 2,
            },
        },
        {
            "name": "no-latest-tag",
            "severity": "error",
            "resource_types": ["Deployment"],
            "rule": {
                "path": "spec.template.spec.containers[*].image",
                "operator": "not_contains",
                "value": ":latest",
            },
        },
    ]

    live_resources = [
        {
            "kind": "Deployment",
            "metadata": {"name": "my-app", "namespace": "default"},
            "spec": {
                "replicas": 1,  # Fails gte 2
                "template": {
                    "spec": {
                        "containers": [
                            {"name": "app", "image": "nginx:latest"}  # Fails not_contains :latest
                        ]
                    }
                },
            },
        }
    ]

    violations = evaluate(live_resources, policies)

    assert len(violations) == 2
    names = [v.policy_name for v in violations]
    assert "replica-count-policy" in names
    assert "no-latest-tag" in names
