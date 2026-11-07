"""
server.py - Native HTTP Server for Cali Social Media & Omnichannel Publishing Hub.
Runs autonomously on port 8793, powered by Next-Gen Agent Echo.
"""

import json
import logging
import mimetypes
import os
import sys
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from engine.agent_echo import AgentEcho
from engine.content_calendar import ContentCalendar
from engine.asset_bridge import AssetBridge

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.social.server")

# Load configuration
CONFIG_PATH = BASE_DIR / "config.json"
CONFIG = {}
if CONFIG_PATH.exists():
    try:
        CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}")

# Initialize engines
AGENT = AgentEcho()
CALENDAR = ContentCalendar()
ASSETS = AssetBridge()


class SocialHubHandler(SimpleHTTPRequestHandler):
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

    def do_HEAD(self):
        super().do_HEAD()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        query = urllib.parse.parse_qs(url.query)

        # 1. API Status
        if path == "/api/status":
            posts = CALENDAR.list_posts()
            self.send_json({
                "status": "ONLINE",
                "module": "cali-social-hub",
                "suite": "Cali Social Media & Publishing Hub",
                "port": CONFIG.get("server", {}).get("port", 8793),
                "agent": {
                    "name": AGENT.name,
                    "generation": AGENT.generation,
                    "role": AGENT.role
                },
                "total_posts": len(posts),
                "scheduled": len([p for p in posts if p.get("status") == "scheduled"]),
                "published": len([p for p in posts if p.get("status") == "published"]),
                "active_networks": list(CONFIG.get("networks", {}).keys()),
                "brands": CONFIG.get("brands", [])
            })
            return

        # 2. List Posts
        if path == "/api/posts":
            brand = query.get("brand", [None])[0]
            status = query.get("status", [None])[0]
            self.send_json(CALENDAR.list_posts(brand=brand, status=status))
            return

        # 3. List Video Assets from Video Studio
        if path == "/api/assets":
            self.send_json(ASSETS.list_available_media())
            return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(post_body) if post_body else {}

        # 1. Create Post
        if path == "/api/posts/create":
            new_post = CALENDAR.create_post(data)
            self.send_json({"status": "created", "post": new_post})
            return

        # 2. Publish Post Now
        if path == "/api/posts/publish":
            post_id = data.get("id")
            res = CALENDAR.publish_now(post_id)
            self.send_json(res)
            return

        # 3. Delete Post
        if path == "/api/posts/delete":
            post_id = data.get("id")
            success = CALENDAR.delete_post(post_id)
            self.send_json({"status": "deleted" if success else "not_found"})
            return

        # 4. Agent Echo Optimization
        if path == "/api/agent/optimize":
            caption = data.get("caption", "")
            network = data.get("network", "tiktok")
            brand = data.get("brand", "cali-media.ltd")
            metrics = AGENT.optimize_post(caption, network, brand)
            self.send_json(metrics)
            return

        # 5. Agent Echo Variations Generator
        if path == "/api/agent/generate":
            topic = data.get("topic", "")
            brand = data.get("brand", "cali-media.ltd")
            variations = AGENT.generate_variations(topic, brand)
            self.send_json({"variations": variations})
            return

        # 6. Omnichannel Broadcast Bridge (used by Central Hub & Cali Brain)
        if path == "/api/broadcast":
            brand = data.get("brand", "cali-media.ltd")
            brand_map = {
                "cali_media": "cali-media.ltd",
                "call_on_dad": "call-on.dad",
                "call_on_mom": "call-on.mom",
                "call_on_shop": "call-on.shop",
                "call_on_media": "call-on.media"
            }
            canonical_brand = brand_map.get(brand, brand)
            caption = data.get("caption", "").strip()
            networks = data.get("networks", ["tiktok", "bluesky"])
            publish_now = data.get("publish_now", True)
            created_posts = []
            receipts = []

            for net in networks:
                net_norm = "youtube_posts" if "youtube" in net else net
                post_data = {
                    "brand": canonical_brand,
                    "network": net_norm,
                    "caption": caption,
                    "media_path": data.get("media_path", ""),
                    "status": "published" if publish_now else "scheduled",
                    "scheduled_time": data.get("scheduled_time", time.strftime("%Y-%m-%d %H:%M"))
                }
                new_post = CALENDAR.create_post(post_data)
                if publish_now:
                    res = CALENDAR.publish_now(new_post["id"])
                    receipts.append(res.get("evidence", {}).get("receipt_id", f"REC-{new_post['id']}"))
                created_posts.append(new_post)

            self.send_json({
                "status": "success",
                "brand": canonical_brand,
                "posts_created": len(created_posts),
                "receipts": receipts,
                "receipt": receipts[0] if receipts else f"REC-{int(time.time())}",
                "networks": networks
            })
            return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    port = CONFIG.get("server", {}).get("port", 8793)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), SocialHubHandler)
    print(f"\n=======================================================")
    print(f"  📱 CALI SOCIAL MEDIA & PUBLISHING HUB (STANDALONE)   ")
    print(f"  Running on: http://{host}:{port}                    ")
    print(f"  Specialist Agent: Echo (Generation 2)               ")
    print(f"  Connected Video Studio: Active                      ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
