"""
server.py - Native HTTP Server for Cali Dev & Code Release Workbench
Runs independently on port 8792, providing Git repository inspection,
side-by-side diffs, secret leak prevention, and safe patch reviews.
"""

import json
import logging
import mimetypes
import os
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from engine.dev_engine import DEV

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.dev.server")

PORT = 8792


class DevHandler(SimpleHTTPRequestHandler):
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
        params = urllib.parse.parse_qs(url.query)

        if path == "/api/status":
            self.send_json({"status": "ONLINE", "module": "cali-dev-workbench", "port": PORT, "version": "1.0.0"})
            return

        if path == "/api/dev/git":
            self.send_json(DEV.get_git_status())
            return

        if path == "/api/dev/diff":
            file_path = params.get("file", [None])[0]
            self.send_json(DEV.get_file_diff(file_path))
            return

        if path == "/api/dev/security":
            self.send_json(DEV.scan_for_secrets())
            return

        if path == "/api/dev/patches":
            self.send_json({"patches": DEV.get_patch_proposals()})
            return

        if path == "/api/dev/receipts":
            self.send_json({"receipts": DEV.get_deployment_receipts()})
            return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(post_body) if post_body else {}

        if path == "/api/dev/patches":
            res = DEV.create_patch_proposal(data)
            self.send_json(res)
            return

        if path == "/api/dev/patches/apply":
            proposal_id = int(data.get("id", 0))
            res = DEV.apply_patch(proposal_id)
            self.send_json(res)
            return

        if path == "/api/dev/patches/reject":
            proposal_id = int(data.get("id", 0))
            res = DEV.reject_patch(proposal_id)
            self.send_json(res)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), DevHandler)
    logger.info(f"Cali Dev & Code Release Workbench running on http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Dev Workbench server stopped.")


if __name__ == "__main__":
    run_server()

