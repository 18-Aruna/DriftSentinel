"""Local live dashboard for DriftSentinel scans.

Serves a browser dashboard that reruns the configured scan whenever the report
is requested and refreshes the report periodically in the browser.
"""

import argparse
import html
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from driftsentinel.config import load_config
from driftsentinel.main import run_pipeline


class LiveDashboardHandler(BaseHTTPRequestHandler):
    """Serve the live shell and freshly generated DriftSentinel report."""

    config_path = "config.yaml"
    refresh_seconds = 10

    def log_message(self, format, *args):
        """Keep the dashboard terminal output concise."""
        print(f"[dashboard] {format % args}")

    def _send(self, content: str, content_type: str, status: int = 200) -> None:
        payload = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(self._dashboard_html(), "text/html; charset=utf-8")
            return
        if path == "/report":
            self._serve_report()
            return
        self._send("Not found", "text/plain; charset=utf-8", 404)

    def _dashboard_html(self) -> str:
        interval = self.refresh_seconds * 1000
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DriftSentinel Live Dashboard</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin: 0; background: #020617; color: #e2e8f0; font-family: system-ui, sans-serif; }}
    header {{ align-items: center; background: #0f172a; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; padding: 12px 20px; }}
    h1 {{ font-size: 18px; margin: 0; }}
    #status {{ color: #94a3b8; font-size: 13px; }}
    iframe {{ border: 0; display: block; height: calc(100vh - 54px); width: 100%; }}
  </style>
</head>
<body>
  <header><h1>DriftSentinel Live Dashboard</h1><span id="status">Loading scan...</span></header>
  <iframe id="report" title="Latest DriftSentinel report" src="/report"></iframe>
  <script>
    const frame = document.getElementById("report");
    const status = document.getElementById("status");
    function refreshReport() {{
      status.textContent = "Scanning...";
      frame.src = "/report?ts=" + Date.now();
    }}
    frame.addEventListener("load", () => {{
      status.textContent = "Last refreshed: " + new Date().toLocaleTimeString();
    }});
    setInterval(refreshReport, {interval});
  </script>
</body>
</html>"""

    def _serve_report(self) -> None:
        try:
            run_pipeline(self.config_path)
            config = load_config(self.config_path)
            report_path = os.path.join(
                config.reporting.html_output_dir, "drift_report_latest.html"
            )
            with open(report_path, "r", encoding="utf-8") as report_file:
                self._send(report_file.read(), "text/html; charset=utf-8")
        except Exception as error:
            message = html.escape(f"Live scan failed: {error}")
            self._send(
                f"<html><body><h1>Live scan failed</h1><p>{message}</p></body></html>",
                "text/html; charset=utf-8",
                500,
            )


def serve(host: str = "127.0.0.1", port: int = 8765, config_path: str = "config.yaml", refresh_seconds: int = 10) -> None:
    """Start the local live dashboard server."""
    if refresh_seconds <= 0:
        raise ValueError("refresh_seconds must be greater than zero")

    handler = LiveDashboardHandler
    handler.config_path = config_path
    handler.refresh_seconds = refresh_seconds
    server = ThreadingHTTPServer((host, port), handler)
    print(f"DriftSentinel live dashboard: http://{host}:{port}")
    print(f"Refreshing every {refresh_seconds} seconds. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping live dashboard.")
    finally:
        server.server_close()


def main() -> None:
    """Parse command-line options and start the dashboard."""
    parser = argparse.ArgumentParser(description="Run the DriftSentinel live dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind (default: localhost)")
    parser.add_argument("--port", type=int, default=8765, help="Dashboard port (default: 8765)")
    parser.add_argument("--config", default="config.yaml", help="DriftSentinel config path")
    parser.add_argument("--interval", type=int, default=10, help="Refresh interval in seconds")
    args = parser.parse_args()
    serve(args.host, args.port, args.config, args.interval)


if __name__ == "__main__":
    main()
