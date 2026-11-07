"""
server.py - Native HTTP Server for Cali Website Health & Review Centre.
Runs on Port 8796. Provides REST APIs for multi-domain uptime, SSL, and Overwatch review queue.
"""

import json
import logging
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(BASE_DIR))

from engine.health_monitor import HealthMonitor
from engine.client_auditor import ClientWebsiteAuditor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.health.server")

CONFIG_PATH = BASE_DIR / "config.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}

MONITOR = HealthMonitor(CONFIG)
AUDITOR = ClientWebsiteAuditor()


class HealthRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "ui"), **kwargs)

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/api/status":
            self.send_json({
                "status": "online",
                "port": CONFIG.get("server", {}).get("port", 8796),
                "agent": CONFIG.get("agent", {}),
                "domains_monitored": len(CONFIG.get("monitored_domains", []))
            })
            return

        if path == "/api/health/check":
            results = MONITOR.check_all_endpoints()
            self.send_json(results)
            return

        if path == "/api/review/queue":
            queue = MONITOR.get_review_queue()
            self.send_json(queue)
            return

        # Client Website Audit History
        if path == "/api/audit/history":
            history = AUDITOR.load_history()
            self.send_json(history)
            return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        data = json.loads(body) if body else {}

        # Run Client Website Health Check
        if path == "/api/audit/client":
            domain = data.get("domain", "").strip()
            if not domain:
                self.send_json({"error": "Missing domain parameter"}, status=400)
                return
            result = AUDITOR.audit_url(domain)
            self.send_json(result)
            return

        self.send_json({"error": "Not Found"}, status=404)


def run_server():
    port = CONFIG.get("server", {}).get("port", 8796)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), HealthRequestHandler)
    print(f"\n=======================================================")
    print(f"  🏥 CALI WEBSITE HEALTH CHECKER & REVIEW CENTRE      ")
    print(f"  Web Dashboard: http://{host}:{port}                 ")
    print(f"  5 Monitored Domains · Uptime Kuma · SSL Tracking    ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

