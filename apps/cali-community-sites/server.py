"""
server.py - Native HTTP Server for Cali Community Sites & Shop Suite.
Runs on Port 8795. Provides REST APIs for Printful sync and community initiatives.
"""

import json
import logging
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(BASE_DIR))

from engine.shop_sync import ShopManager
from engine.community_manager import CommunityManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.community.server")

CONFIG_PATH = BASE_DIR / "config.json"
CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}

SHOP = ShopManager(CONFIG)
COMMUNITY = CommunityManager(CONFIG)


class CommunityRequestHandler(SimpleHTTPRequestHandler):
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
                "module": "cali-community-sites",
                "port": CONFIG.get("server", {}).get("port", 8795),
                "agent": CONFIG.get("agent", {}),
                "sites_monitored": 3,
                "products_count": len(SHOP.get_products())
            })
            return

        if path == "/api/shop/products":
            self.send_json(SHOP.get_products())
            return

        if path == "/api/community/stats":
            self.send_json(COMMUNITY.get_community_stats())
            return

        if path == "/api/guides":
            # Return all community guides: both £1.99 print-offs and free onboarding guides
            guides_data = {
                "print_off_guides": [
                    {
                        "id": "boiler-pressure-dropping-in-sub-zero-weather",
                        "title": "Call-On Dad Emergency Guide: Boiler Pressure Dropping in Sub-Zero Weather (DIY Diagnosis & Reset Checklist)",
                        "price": "£1.99",
                        "price_gbp": 1.99,
                        "author": "Trevor",
                        "category": "Print-Off Emergency Guide",
                        "format": "Printable A4 Document + Interactive Checklist",
                        "local_url": "/guides/boiler-pressure-dropping-in-sub-zero-weather.html",
                        "shop_url": "https://call-on.shop/guides/boiler-pressure-dropping-in-sub-zero-weather",
                        "video_stream": "http://127.0.0.1:8790/stream/exports/trend_videos/trend_1793994085_trevor.mp4"
                    }
                ],
                "dashboard_guides": [
                    {
                        "id": "dad-volunteer",
                        "title": "Call-On Dad Volunteer Dashboard: Getting Started",
                        "price": "Free Community Resource",
                        "price_gbp": 0.0,
                        "audience": "Volunteers & Mentors",
                        "local_url": "/guides/dashboard/dad-volunteer.html",
                        "pdf_url": "https://call-on.shop/guides/dashboard/dad-volunteer.pdf",
                        "video_url": "https://call-on.dad/assets/onboarding-20261023/volunteer.mp4",
                        "blog_url": "https://call-on.dad/blog/getting-started-dad-volunteer-dashboard"
                    },
                    {
                        "id": "dad-user",
                        "title": "Call-On Dad User Dashboard: Getting Started",
                        "price": "Free Community Resource",
                        "price_gbp": 0.0,
                        "audience": "Parents & Advice Seekers",
                        "local_url": "/guides/dashboard/dad-user.html",
                        "pdf_url": "https://call-on.shop/guides/dashboard/dad-user.pdf",
                        "video_url": "https://call-on.dad/assets/onboarding-20261023/user.mp4",
                        "blog_url": "https://call-on.dad/blog/getting-started-dad-user-dashboard"
                    },
                    {
                        "id": "mom-volunteer",
                        "title": "Call-On Mom Volunteer Dashboard: Getting Started",
                        "price": "Free Community Resource",
                        "price_gbp": 0.0,
                        "audience": "Volunteers & Mentors",
                        "local_url": "/guides/dashboard/mom-volunteer.html",
                        "pdf_url": "https://call-on.shop/guides/dashboard/mom-volunteer.pdf",
                        "video_url": "https://call-on.mom/assets/onboarding-20261023/volunteer.mp4",
                        "blog_url": "https://call-on.mom/blog/getting-started-mom-volunteer-dashboard"
                    },
                    {
                        "id": "mom-user",
                        "title": "Call-On Mom User Dashboard: Getting Started",
                        "price": "Free Community Resource",
                        "price_gbp": 0.0,
                        "audience": "Mothers & Families",
                        "local_url": "/guides/dashboard/mom-user.html",
                        "pdf_url": "https://call-on.shop/guides/dashboard/mom-user.pdf",
                        "video_url": "https://call-on.mom/assets/onboarding-20261023/user.mp4",
                        "blog_url": "https://call-on.mom/blog/getting-started-mom-user-dashboard"
                    }
                ]
            }
            self.send_json(guides_data)
            return

        # Serve static guides from ct500/shop/guides
        if path.startswith("/guides/") or path.startswith("/shop/guides/"):
            subpath = path.replace("/shop/guides/", "").replace("/guides/", "")
            guide_file = Path("d:/The Cali Project/sites/ct500/shop/guides") / subpath
            if guide_file.exists() and guide_file.is_file():
                self.send_response(200)
                if subpath.endswith(".html"):
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                elif subpath.endswith(".pdf"):
                    self.send_header("Content-Type", "application/pdf")
                else:
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                data = guide_file.read_bytes()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/api/shop/sync":
            res = SHOP.sync_with_printful()
            self.send_json(res)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    port = CONFIG.get("server", {}).get("port", 8795)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), CommunityRequestHandler)
    print(f"\n=======================================================")
    print(f"  🌐 CALI COMMUNITY SITES & SHOP SUITE                ")
    print(f"  Web Dashboard: http://{host}:{port}                 ")
    print(f"  Call-On Dad · Call-On Mom · Call-On Shop Sync        ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

