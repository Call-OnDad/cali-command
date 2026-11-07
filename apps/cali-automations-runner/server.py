"""
server.py - Native HTTP Server for Cali Autonomous Daily Briefing & Automations Runner
Runs independently on port 8794, providing scheduled tasks, executive briefings,
cross-suite telemetry aggregation, and execution logs.
"""

import json
import logging
import urllib.parse
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from engine.automation_engine import AUTOMATIONS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.automations.server")

PORT = 8794


class AutomationsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "ui"), **kwargs)

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/api/status":
            self.send_json({"status": "ONLINE", "module": "cali-automations-runner", "port": PORT, "version": "1.0.0"})
            return

        if path == "/api/briefings/latest":
            self.send_json(AUTOMATIONS.get_latest_briefing())
            return

        if path == "/api/briefings":
            self.send_json({"briefings": AUTOMATIONS.get_all_briefings()})
            return

        if path == "/api/automations/jobs":
            self.send_json({"jobs": AUTOMATIONS.get_jobs()})
            return

        if path == "/api/automations/logs":
            self.send_json({"logs": AUTOMATIONS.get_logs()})
            return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(post_body) if post_body else {}

        if path == "/api/briefings/generate":
            res = AUTOMATIONS.compile_daily_briefing()
            self.send_json(res)
            return

        if path == "/api/automations/toggle":
            job_id = data.get("job_id")
            enabled = bool(data.get("enabled", True))
            res = AUTOMATIONS.toggle_job(job_id, enabled)
            self.send_json(res)
            return

        if path == "/api/automations/run":
            job_id = data.get("job_id")
            res = AUTOMATIONS.run_job(job_id)
            self.send_json(res)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), AutomationsHandler)
    logger.info(f"Cali Autonomous Daily Briefing & Automations Runner on http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Automations Runner server stopped.")


if __name__ == "__main__":
    run_server()

