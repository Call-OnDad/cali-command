"""
server.py - Native HTTP Server for Cali Website Creator, Client Outsell Prototyper & 2026 Design Vault.
Runs independently on port 8789, providing UI dashboard, live canvas rendering,
token extraction, and static export management.
"""

import json
import logging
import os
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from engine.site_builder import SiteBuilder
from engine.token_extractor import extract_tokens_from_url, extract_tokens_from_html, DESIGN_ARCHETYPES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.website_creator")

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
UI_DIR = BASE_DIR / "ui"

def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to read config.json: {e}")
    return {"server": {"port": 8789, "host": "127.0.0.1"}}

CONFIG = load_config()
BUILDER = SiteBuilder(CONFIG)

class CreatorRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

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
                "module": "cali-website-creator",
                "port": CONFIG.get("server", {}).get("port", 8789),
                "agent": CONFIG.get("agent", {}),
                "templates_available": len(BUILDER.list_templates()),
                "archetypes_available": len(BUILDER.list_archetypes()),
                "sites_published": len(BUILDER.list_generated_sites())
            })
            return

        if path == "/api/templates":
            self.send_json(BUILDER.list_templates())
            return

        if path == "/api/vault/archetypes":
            self.send_json(BUILDER.list_archetypes())
            return

        if path == "/api/sites/list":
            self.send_json(BUILDER.list_generated_sites())
            return

        # Serve preview files from exports/ if path starts with /preview/
        if path.startswith("/preview/"):
            parts = path.strip("/").split("/")
            if len(parts) >= 2:
                site_id = parts[1]
                subfile = parts[2] if len(parts) > 2 else "index.html"
                target_file = BUILDER.export_dir / site_id / subfile
                if target_file.exists() and target_file.is_file():
                    mime = "text/html" if subfile.endswith(".html") else "text/css" if subfile.endswith(".css") else "text/plain"
                    data = target_file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/api/vault/extract-tokens":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw) if raw else {}
            target_url = data.get("url", "")
            target_html = data.get("html", "")

            if target_html:
                tokens = extract_tokens_from_html(target_html, base_url=target_url)
            elif target_url:
                tokens = extract_tokens_from_url(target_url)
            else:
                tokens = {
                    "error": "Please provide a valid URL or raw HTML snippet to inspect.",
                    "recommended_archetype": "bento-modern-saas"
                }
            self.send_json(tokens)
            return

        if path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw) if raw else {}

            title = data.get("title", "Emergency Plumbing & Heating")
            business_name = data.get("business_name", title)
            city = data.get("city", "London & Greater London")
            phone = data.get("phone", "020 7946 0991")
            headline = data.get("headline", "24/7 Emergency Plumbing & Gas Safe Engineers")
            subhead = data.get("subhead", "On-site within 45 minutes across London. Transparent fixed rates.")
            theme = data.get("theme", "trust-blue")
            archetype = data.get("archetype", "high-trust-trades")
            cta_text = data.get("cta_text", "Call Engineer Now")
            domain = data.get("domain", "prospect-preview.call-on.media")
            testimonial = data.get("testimonial", {
                "quote": "Arrived within 35 minutes when our boiler burst at 2 AM. Top-notch work and fair pricing.",
                "author": f"Homeowner · {city}"
            })
            features = data.get("features", [
                {"title": "Emergency Burst Pipe Repair", "desc": "Rapid arrival with thermal imaging diagnostics.", "price": "From £85/hr"},
                {"title": "Boiler Breakdown & Service", "desc": "Gas Safe registered boiler diagnostics and repair.", "price": "Fixed £95 Callout"},
                {"title": "Commercial Drain Clearing", "desc": "High pressure jetting and CCTV drain inspection.", "price": "Free Estimate"}
            ])

            result = BUILDER.generate_page(
                title=title,
                headline=headline,
                subhead=subhead,
                theme=theme,
                cta_text=cta_text,
                features=features,
                domain=domain,
                business_name=business_name,
                phone=phone,
                city=city,
                testimonial=testimonial,
                archetype=archetype
            )
            self.send_json(result)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    port = CONFIG.get("server", {}).get("port", 8789)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), CreatorRequestHandler)
    print(f"\n=======================================================")
    print(f"  🌐  CALI WEBSITE CREATOR & 2026 DESIGN VAULT         ")
    print(f"  Web Dashboard: http://{host}:{port}                 ")
    print(f"  Agent Scribe · Port 8789 · CT500 Caddy Deployment   ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
