"""
server.py - Native HTTP Server for Cali Security Findings & Threat Radar.
Runs on Port 8797. Provides REST APIs for vulnerability scanning, TLS grading, and CrowdSec blocklists.
"""

import json
import logging
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(BASE_DIR))

from engine.security_scanner import SecurityScanner
from engine.bounty_engagement_manager import BountyEngagementManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.security.server")

CONFIG_PATH = BASE_DIR / "config.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}

SCANNER = SecurityScanner(CONFIG)
BOUNTY_MGR = BountyEngagementManager()


class SecurityRequestHandler(SimpleHTTPRequestHandler):
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
                "port": CONFIG.get("server", {}).get("port", 8797),
                "agent": CONFIG.get("agent", {}),
                "domains_shielded": len(CONFIG.get("target_domains", []))
            })
            return

        if path == "/api/security/scan":
            posture = SCANNER.get_security_posture()
            self.send_json(posture)
            return

        # Authorised Client Engagements
        if path == "/api/engagements":
            engagements = BOUNTY_MGR.list_engagements()
            self.send_json(engagements)
            return

        # Bug Bounty Programmes
        if path == "/api/bounty/programs":
            programs = BOUNTY_MGR.list_bounty_programs()
            self.send_json(programs)
            return

        # T3MP3ST Autonomous Pentest Agent (CT115)
        if path == "/api/t3mp3st/status":
            status = BOUNTY_MGR.get_t3mp3st_status()
            self.send_json(status)
            return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        data = json.loads(body) if body else {}

        if path == "/api/engagements/add":
            name = data.get("name", "").strip()
            targets = data.get("targets", [])
            note = data.get("note", "").strip()
            client = data.get("client", "").strip()
            expires = data.get("expires", "30 Days")
            if not name or not targets:
                self.send_json({"error": "Name and targets are required"}, status=400)
                return
            res = BOUNTY_MGR.add_engagement(name, targets, note, client, expires)
            self.send_json(res)
            return

        if path == "/api/bounty/programs/add":
            platform = data.get("platform", "HackerOne").strip()
            name = data.get("name", "").strip()
            policy_url = data.get("policy_url", "").strip()
            scope = data.get("scope", "").strip()
            if not name:
                self.send_json({"error": "Programme name required"}, status=400)
                return
            res = BOUNTY_MGR.add_bounty_program(platform, name, policy_url, scope)
            self.send_json(res)
            return

        self.send_json({"error": "Not Found"}, status=404)


def run_server():
    port = CONFIG.get("server", {}).get("port", 8797)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), SecurityRequestHandler)
    print(f"\n=======================================================")
    print(f"  🛡️ CALI SECURITY FINDINGS & THREAT RADAR            ")
    print(f"  Web Dashboard: http://{host}:{port}                 ")
    print(f"  Cloudflare WAF · CrowdSec Defense · TLS A+ Posture  ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

