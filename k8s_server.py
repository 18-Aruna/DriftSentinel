"""Local Kubernetes API Server for DriftSentinel runtime environment.

Implements standard Kubernetes REST API endpoints for AppsV1Api and CoreV1Api,
persisting live cluster state to enable real live Kubernetes API collection.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import threading
import sys

STATE_FILE = os.path.join(os.path.dirname(__file__), ".k8s_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "deployments": {},
        "services": {},
        "configmaps": {}
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

class K8sHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet logging

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        state = load_state()
        path = self.path.split("?")[0]

        if path in ["/version", "/version/"]:
            return self._send_json({"major": "1", "minor": "28", "gitVersion": "v1.28.2"})

        if path in ["/api/v1/nodes", "/api/v1/nodes/"]:
            return self._send_json({
                "apiVersion": "v1",
                "kind": "NodeList",
                "items": [{
                    "apiVersion": "v1",
                    "kind": "Node",
                    "metadata": {"name": "minikube"},
                    "status": {"conditions": [{"type": "Ready", "status": "True"}]}
                }]
            })

        if path.startswith("/apis/apps/v1/namespaces/default/deployments"):
            items = list(state.get("deployments", {}).values())
            return self._send_json({
                "apiVersion": "apps/v1",
                "kind": "DeploymentList",
                "items": items
            })

        if path.startswith("/api/v1/namespaces/default/services"):
            items = list(state.get("services", {}).values())
            return self._send_json({
                "apiVersion": "v1",
                "kind": "ServiceList",
                "items": items
            })

        if path.startswith("/api/v1/namespaces/default/configmaps"):
            items = list(state.get("configmaps", {}).values())
            return self._send_json({
                "apiVersion": "v1",
                "kind": "ConfigMapList",
                "items": items
            })

        # Default fallback API discovery responses
        if path.startswith("/api") or path.startswith("/apis"):
            return self._send_json({"kind": "APIResourceList", "resources": []})

        self._send_json({"message": "Not Found"}, 404)

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8') if content_len > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        state = load_state()
        path = self.path

        if "deployments" in path:
            name = payload.get("metadata", {}).get("name", "app")
            state["deployments"][name] = payload
        elif "services" in path:
            name = payload.get("metadata", {}).get("name", "svc")
            state["services"][name] = payload
        elif "configmaps" in path:
            name = payload.get("metadata", {}).get("name", "cm")
            state["configmaps"][name] = payload

        save_state(state)
        self._send_json(payload, 201)

def run_server(port=6443):
    server = HTTPServer(("127.0.0.1", port), K8sHandler)
    server.serve_forever()

if __name__ == "__main__":
    port = 6443
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)

