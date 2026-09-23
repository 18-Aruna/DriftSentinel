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

## Live Dashboard

Start a local dashboard that reruns the scan and refreshes the visual report automatically:

```bash
python -m driftsentinel.live_dashboard
```

Open `http://127.0.0.1:8765` in a browser. The default refresh interval is 10 seconds. It can be changed with `--interval`, and a different configuration or port can be supplied:

```bash
python -m driftsentinel.live_dashboard --config config.yaml --port 8766 --interval 5
```

The dashboard is intended for local demonstrations. It binds to localhost by default and does not provide authentication or multi-user access.

### Local Simulator Demo

When using the included local simulator instead of a real Minikube cluster, start the API server and deploy the sample release before opening the dashboard:

```powershell
# Terminal 1
python k8s_server.py 6443

# Terminal 2
.\bin\helm.cmd install sample-app .\charts\sample-app --namespace default
python -m driftsentinel.live_dashboard
```

Keep the API server and dashboard terminals running. If the API server is stopped, the dashboard correctly reports a scan error because no live Kubernetes state can be collected.

## Scan Results and Exit Codes

DriftSentinel reports unmanaged live resources in addition to modified and missing resources. A scan status of `ERROR` means the desired or live state could not be collected; it is not treated as a clean scan.

Exit codes are suitable for CI/CD gates:

- `0` — scan completed with no drift or blocking policy violations
- `1` — drift detected
- `2` — scan or configuration error
- `3` — an `error` severity policy violation was found

## Limitations

- The built-in collector supports Deployments, Services, and ConfigMaps only (no CRDs)
- The included simulator is designed for local Minikube-style demonstrations
- No persistent drift history (each run is independent)
- Auto-healing only supports Helm-based reconciliation

For production use, the next major steps are a dynamic Kubernetes client for arbitrary resources, persistent scan history, watch mode, and approval-controlled healing.

## License

This project is developed as an undergraduate final-year project.
