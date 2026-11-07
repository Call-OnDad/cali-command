"""
server.py - Native HTTP Server for Cali SEO & Search Radar Suite.
Runs autonomously on port 8791, completely decoupled from other Cali systems.
"""

import json
import logging
import mimetypes
import os
import sys
import threading
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from engine.domain_registry import DomainRegistry
from engine.site_crawler import SiteCrawler
from engine.serpbear_client import SerpBearClient
from engine.content_auditor import ContentAuditor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.seo.server")

# Load configuration
CONFIG_PATH = BASE_DIR / "config.json"
CONFIG = {}
if CONFIG_PATH.exists():
    try:
        CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}")

# Initialize engines
REGISTRY = DomainRegistry()
CRAWLER = SiteCrawler(user_agent=CONFIG.get("crawler", {}).get("user_agent"))
SERPBEAR = SerpBearClient(
    endpoint=CONFIG.get("serpbear", {}).get("endpoint", "http://192.168.1.120:3000"),
    api_key=CONFIG.get("serpbear", {}).get("api_key", "")
)
AUDITOR = ContentAuditor()


class SEORadarHandler(SimpleHTTPRequestHandler):
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
            domains = REGISTRY.list_domains()
            ct120_online = SERPBEAR.is_ct120_live()
            total_kw = sum(len(SERPBEAR.get_domain_keywords(d["id"])) for d in domains)

            self.send_json({
                "status": "ONLINE",
                "module": "cali-seo-radar",
                "service": "Cali SEO & Search Radar",
                "port": CONFIG.get("server", {}).get("port", 8791),
                "ct120_serpbear": {
                    "endpoint": SERPBEAR.endpoint,
                    "status": "connected" if ct120_online else "autonomous_fallback_active"
                },
                "total_domains": len(domains),
                "total_keywords_tracked": total_kw,
                "version": "1.0.0"
            })
            return

        # 2. List Domains
        if path == "/api/domains":
            self.send_json(REGISTRY.list_domains())
            return

        # 3. Crawler Report (Cached or Fresh)
        if path == "/api/crawler/report":
            domain_id = query.get("domain", ["cali-media.ltd"])[0]
            report = CRAWLER.load_cached_report(domain_id)
            if not report:
                # Run fresh crawl
                report = CRAWLER.crawl_url(domain_id)
            self.send_json(report)
            return

        # 4. Keywords & Ranks for a Domain
        if path == "/api/keywords":
            domain_id = query.get("domain", ["cali-media.ltd"])[0]
            keywords = SERPBEAR.get_domain_keywords(domain_id)
            self.send_json(keywords)
            return

        # Default static file handler
        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(post_body) if post_body else {}

        # 1. Add Domain
        if path == "/api/domains/add":
            new_domain = REGISTRY.add_domain(data)
            self.send_json({"status": "created", "domain": new_domain})
            return

        # 2. Delete Domain
        if path == "/api/domains/delete":
            domain_id = data.get("id")
            success = REGISTRY.remove_domain(domain_id)
            self.send_json({"status": "deleted" if success else "not_found"})
            return

        # 3. Trigger Live Crawl
        if path == "/api/crawler/run":
            target_url = data.get("url") or data.get("domain", "https://cali-media.ltd")
            report = CRAWLER.crawl_url(target_url)

            # Update health score in registry
            domain_entry = REGISTRY.get_domain(report.get("domain", ""))
            if domain_entry:
                domain_entry["health_score"] = report.get("health_score", 85)
                domain_entry["last_crawled"] = report.get("timestamp")
                REGISTRY.save()

            self.send_json(report)
            return

        # 4. Add Tracked Keyword
        if path == "/api/keywords/add":
            domain_id = data.get("domain", "cali-media.ltd")
            keyword = data.get("keyword", "")
            if not keyword.strip():
                self.send_json({"error": "Keyword cannot be empty"}, status=400)
                return
            kw_entry = SERPBEAR.add_keyword(domain_id, keyword.strip())
            self.send_json({"status": "added", "keyword": kw_entry})
            return

        # 5. Refresh Ranks
        if path == "/api/keywords/refresh":
            domain_id = data.get("domain", "cali-media.ltd")
            updated_kws = SERPBEAR.refresh_ranks(domain_id)
            self.send_json({"status": "refreshed", "keywords": updated_kws})
            return

        # 6. Content SEO Auditor
        if path == "/api/audit/content":
            text = data.get("text", "")
            target_keyword = data.get("target_keyword", "")
            title = data.get("title", "")
            meta_desc = data.get("meta_description", "")
            slug = data.get("slug", "")

            audit_res = AUDITOR.audit_content(
                text=text,
                target_keyword=target_keyword,
                title=title,
                meta_description=meta_desc,
                slug=slug
            )
            self.send_json(audit_res)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    port = CONFIG.get("server", {}).get("port", 8791)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), SEORadarHandler)
    print(f"\n=======================================================")
    print(f"  🔍 CALI SEO & SEARCH RADAR SUITE (STANDALONE)        ")
    print(f"  Running on: http://{host}:{port}                    ")
    print(f"  CT120 SerpBear: {SERPBEAR.endpoint}                 ")
    print(f"  Active Domains: {len(REGISTRY.list_domains())}      ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
