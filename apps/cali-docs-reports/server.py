"""
server.py - Native HTTP Server for Cali Documents, Reports & Knowledge Centre.
Runs on Port 8798. Provides REST APIs for OnlyOffice workspaces, Companies House filings, and audit docs.
"""

import json
import logging
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(BASE_DIR))

from engine.doc_vault import DocVault

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.docs.server")

CONFIG_PATH = BASE_DIR / "config.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}

VAULT = DocVault(CONFIG)


class DocsRequestHandler(SimpleHTTPRequestHandler):
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
            self.send_json({
                "status": "ONLINE",
                "module": "cali-docs-reports",
                "port": CONFIG.get("server", {}).get("port", 8798),
                "agent": CONFIG.get("agent", {}),
                "documents_indexed": len(VAULT.list_documents())
            })
            return

        if path == "/api/docs/list":
            docs = VAULT.list_documents()
            self.send_json(docs)
            return

        if path == "/api/knowledge/search":
            query = urllib.parse.parse_qs(url.query).get("q", [""])[0]
            results = VAULT.search_knowledge(query)
            self.send_json({"query": query, "count": len(results), "results": results})
            return

        if path == "/api/corporate/filings":
            filings = VAULT.get_corporate_filings()
            self.send_json(filings)
            return

        super().do_GET()


def run_server():
    port = CONFIG.get("server", {}).get("port", 8798)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), DocsRequestHandler)
    print(f"\n=======================================================")
    print(f"  📄 CALI DOCS, REPORTS & KNOWLEDGE CENTRE            ")
    print(f"  Web Dashboard: http://{host}:{port}                 ")
    print(f"  OnlyOffice Bridge · Companies House · Corporate SOPs")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

