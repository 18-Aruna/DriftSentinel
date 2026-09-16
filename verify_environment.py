"""
DriftSentinel Environment Verification Script
==============================================
Run this script to verify that all prerequisites are installed
and the development environment is ready for Milestone 1.

Usage (PowerShell):
    python verify_environment.py

This script checks:
    1. Python version >= 3.9
    2. Required Python packages (kubernetes, PyYAML, deepdiff, pytest)
    3. kubectl connectivity
    4. Helm CLI availability
    5. Minikube cluster status
    6. Sample Helm chart exists
    7. Sample app deployment (if deployed)
"""

import sys
import subprocess
import os


def print_header():
    """Print the verification header."""
    print("=" * 60)
    print("DriftSentinel Environment Verification")
    print("=" * 60)
    print()


def check(label, status, detail=""):
    """Print a single check result."""
    # Pad the label for aligned output
    padded = f"[CHECK] {label} ".ljust(45, ".")
    if status:
        print(f"{padded} OK{' (' + detail + ')' if detail else ''}")
    else:
        print(f"{padded} FAILED{' (' + detail + ')' if detail else ''}")
    return status


def check_python_version():
    """Verify Python >= 3.9."""
    major, minor = sys.version_info[:2]
    version_str = f"{major}.{minor}.{sys.version_info[2]}"
    return check("Python version", major == 3 and minor >= 9, version_str)


def check_package(package_name):
    """Verify a Python package is importable."""
    try:
        __import__(package_name)
        return check(f"{package_name} client", True, "installed")
    except ImportError:
        return check(
            f"{package_name} client", False,
            f"not installed — run: pip install {package_name}"
        )


def check_command(label, command, success_indicator=None):
    """
    Run a shell command and check if it succeeds.

    Args:
        label: Human-readable label for the check.
        command: Command as a list of strings.
        success_indicator: Optional string to search for in stdout.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()

        if result.returncode != 0:
            error_msg = result.stderr.strip().split("\n")[0] if result.stderr else "unknown error"
            return check(label, False, error_msg)

        if success_indicator and success_indicator not in output:
            return check(label, False, f"unexpected output: {output[:60]}")

        # Extract a short detail from the output
        detail = output.split("\n")[0][:40] if output else "ok"
        return check(label, True, detail)

    except FileNotFoundError:
        return check(label, False, f"'{command[0]}' not found in PATH")
    except subprocess.TimeoutExpired:
        return check(label, False, "command timed out")
    except Exception as e:
        return check(label, False, str(e)[:60])


def check_minikube_status():
    """Check if Minikube cluster is running."""
    try:
        result = subprocess.run(
            ["minikube", "status", "--format", "{{.Host}}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        status = result.stdout.strip()
        if status == "Running":
            return check("Minikube cluster", True, "Running")
        else:
            return check(
                "Minikube cluster", False,
                f"status={status} — run: minikube start"
            )
    except FileNotFoundError:
        return check("Minikube cluster", False, "minikube not found in PATH")
    except Exception as e:
        return check("Minikube cluster", False, str(e)[:60])


def check_sample_chart():
    """Verify the sample Helm chart directory exists."""
    chart_file = os.path.join("charts", "sample-app", "Chart.yaml")
    exists = os.path.isfile(chart_file)
    return check(
        "Sample chart exists", exists,
        chart_file if exists else f"{chart_file} not found"
    )


def check_sample_deployment():
    """Check if the sample-app is deployed to the cluster."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployment", "sample-app-nginx",
             "-n", "default", "-o", "name"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and "sample-app-nginx" in result.stdout:
            return check("Sample app deployed", True,
                         "deployment sample-app-nginx found")
        else:
            return check("Sample app deployed", False,
                         "not deployed — run: helm install sample-app ./charts/sample-app")
    except FileNotFoundError:
        return check("Sample app deployed", False, "kubectl not found")
    except Exception as e:
        return check("Sample app deployed", False, str(e)[:60])


def main():
    """Run all environment checks."""
    print_header()

    results = []

    # Python version
    results.append(check_python_version())

    # Python packages
    results.append(check_package("kubernetes"))
    results.append(check_package("yaml"))
    results.append(check_package("deepdiff"))
    results.append(check_package("pytest"))

    # External tools
    results.append(check_command(
        "kubectl reachable",
        ["kubectl", "cluster-info"],
    ))
    results.append(check_command(
        "helm available",
        ["helm", "version", "--short"],
    ))

    # Minikube
    results.append(check_minikube_status())

    # Project files
    results.append(check_sample_chart())

    # Deployment (optional — may not be deployed yet)
    results.append(check_sample_deployment())

    # Summary
    print()
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if all(results):
        print("All checks passed. Environment is ready for Milestone 1.")
    else:
        failed = total - passed
        print(f"{passed}/{total} checks passed. {failed} check(s) failed.")
        print("Fix the failed checks above before proceeding.")
    print("=" * 60)

    # Return exit code
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
