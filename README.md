# DriftSentinel

A local GitOps drift detection and auto-healing tool for Kubernetes.

## What It Does

DriftSentinel compares the **desired state** (defined in a Helm chart) against the **live state** (running in a Minikube cluster) and reports any configuration drift. It can also evaluate compliance policies and optionally auto-heal detected drift.

## Features

- **Drift Detection** — Field-level comparison of Helm-defined desired state vs live Kubernetes state
- **Normalization** — Strips Kubernetes-injected fields to avoid false positives
- **Policy Engine** — Evaluates live resources against YAML-defined compliance rules
- **Auto-Healing** — Optionally reapplies the Helm release to fix detected drift
- **Reporting** — CLI table output and self-contained HTML reports

## Prerequisites

- Python 3.9+
- Minikube
- kubectl
- Helm 3
- Git

## Quick Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start Minikube
minikube start

# 3. Deploy the sample application
helm install sample-app ./charts/sample-app --namespace default

# 4. Run DriftSentinel
python -m driftsentinel.main

# 5. Cause some drift and re-run
kubectl scale deployment sample-app-nginx --replicas=5
python -m driftsentinel.main
```

## Configuration

Edit `config.yaml` to configure:
- Helm chart location and release name
- Kubernetes namespace and resource types to monitor
- Policy file location
- Auto-healing (disabled by default)
- Report output settings

## Project Structure

```
driftsentinel/          Main Python package
  collector/            Fetches live state from Kubernetes API
  renderer/             Renders desired state from Helm charts
  detector/             Normalizes and compares states
  policy/               Evaluates compliance policies
  healer/               Auto-heals drift via Helm upgrade
  reporter/             CLI and HTML report generation
charts/sample-app/      Sample Helm chart for testing
policies/               YAML policy definitions
tests/                  Unit and integration tests
```

## Running Tests

```bash
pytest tests/ -v
```

## Limitations

- Supports Deployments, Services, and ConfigMaps only (no CRDs)
- Designed for local Minikube clusters only
- No persistent drift history (each run is independent)
- Auto-healing only supports Helm-based reconciliation

## License

This project is developed as an undergraduate final-year project.
