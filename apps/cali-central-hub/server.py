"""
server.py - Native HTTP Server for Cali Central Command Hub & Mission Control.
Runs on port 8700, serving as the master executive dashboard for all Cali departments.
"""

import json
import logging
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from engine.hub_manager import HubManager
from engine.cali_brain import CaliBrain
from engine.proxmox_bridge import PROXMOX

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.central.server")

CONFIG_PATH = BASE_DIR / "config.json"
CONFIG = {}
if CONFIG_PATH.exists():
    try:
        CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}")

HUB = HubManager()
BRAIN = CaliBrain()


class CentralHubHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "ui"), **kwargs)

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_HEAD(self):
        url = urllib.parse.urlparse(self.path)
        if url.path.startswith("/proxy/"):
            self.do_GET()
            return
        super().do_HEAD()

    def _proxy_request(self, method: str, port: int, subpath: str, data: bytes = None):
        try:
            target_url = f"http://127.0.0.1:{port}{subpath}"
            headers = {}
            for k, v in self.headers.items():
                if k.lower() not in ('host', 'content-length', 'transfer-encoding', 'connection'):
                    headers[k] = v
            req = urllib.request.Request(target_url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                for hk, hv in resp.getheaders():
                    if hk.lower() not in ('transfer-encoding', 'content-length', 'connection'):
                        self.send_header(hk, hv)
                self.send_header('Content-Length', str(len(resp_body)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            for hk, hv in e.headers.items():
                if hk.lower() not in ('transfer-encoding', 'content-length', 'connection'):
                    self.send_header(hk, hv)
            self.send_header('Content-Length', str(len(err_body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            logger.error(f"Proxy error to port {port}{subpath}: {e}")
            self.send_json({"error": f"Failed to connect to module on port {port}", "details": str(e)}, status=502)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # 0. Secure In-App Module Proxy (/proxy/<port>/<subpath>)
        if path.startswith("/proxy/"):
            parts = path.split("/", 3)
            if len(parts) >= 3 and parts[2].isdigit():
                target_port = int(parts[2])
                subpath = "/" + (parts[3] if len(parts) > 3 else "")
                if url.query:
                    subpath += "?" + url.query
                self._proxy_request("GET", target_port, subpath)
                return

        # 1. Fleet Status & Health
        if path == "/api/fleet":
            fleet = HUB.get_fleet_status()
            self.send_json(fleet)
            return

        # 1b. Full Business Management Dashboard (Umami Traffic + Attention + Fleet + Queues)
        if path == "/api/dashboard/full":
            dashboard = HUB.get_full_dashboard()
            self.send_json(dashboard)
            return

        # 1c. Umami Live Traffic
        if path == "/api/traffic":
            hours = int(urllib.parse.parse_qs(url.query).get("hours", [24])[0])
            traffic = HUB.get_traffic_analytics(hours)
            self.send_json(traffic)
            return

        # 2. Unified Incoming Information Event Stream
        if path == "/api/events":
            events = HUB.get_unified_event_stream()
            self.send_json(events)
            return

        # 2b. Executive At-A-Glance Attention Summary
        if path == "/api/attention":
            summary = HUB.get_attention_summary()
            self.send_json(summary)
            return

        # 3. System Telemetry & Disk
        if path == "/api/telemetry":
            telemetry = HUB.get_system_telemetry()
            self.send_json(telemetry)
            return

        # 4. Cali Chat History
        if path == "/api/cali/history":
            history = BRAIN.load_history()
            self.send_json(history)
            return

        # 5. Cali Settings
        if path == "/api/cali/settings":
            settings = BRAIN.get_llm_settings()
            # Mask API key for UI security
            masked = dict(settings)
            if masked.get("api_key"):
                masked["api_key_masked"] = masked["api_key"][:6] + "..." + masked["api_key"][-4:]
            self.send_json(masked)
            return

        # 6. Proxmox & Homelab Infrastructure Overwatch
        if path == "/api/proxmox/overwatch":
            self.send_json(PROXMOX.get_full_overwatch())
            return

        if path == "/api/proxmox/updates":
            self.send_json(PROXMOX.get_fleet_updates())
            return

        if path == "/api/proxmox/backups":
            self.send_json(PROXMOX.get_backup_status())
            return

        if path == "/api/proxmox/pulse":
            self.send_json(PROXMOX.get_pulse_services())
            return

        # Fallback 1: If path is /preview/*, route to Website Creator (:8789)
        if path.startswith("/preview/"):
            subpath = path
            if url.query:
                subpath += "?" + url.query
            self._proxy_request("GET", 8789, subpath)
            return

        # Fallback 2: Check Referer for embedded module (/proxy/<port>/)
        referer = self.headers.get("Referer", "")
        if "/proxy/" in referer:
            ref_match = re.search(r"/proxy/(\d+)(?:/|$)", referer)
            if ref_match:
                target_port = int(ref_match.group(1))
                subpath = path
                if url.query:
                    subpath += "?" + url.query
                self._proxy_request("GET", target_port, subpath)
                return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b""

        # 0. Secure In-App Module Proxy POST (/proxy/<port>/<subpath>)
        if path.startswith("/proxy/"):
            parts = path.split("/", 3)
            if len(parts) >= 3 and parts[2].isdigit():
                target_port = int(parts[2])
                subpath = "/" + (parts[3] if len(parts) > 3 else "")
                if url.query:
                    subpath += "?" + url.query
                self._proxy_request("POST", target_port, subpath, data=raw_body)
                return

        post_body = raw_body.decode("utf-8") if raw_body else ""
        data = json.loads(post_body) if post_body else {}

        # 1. Talk to Cali (Executive AI Chat)
        if path == "/api/cali/chat":
            user_msg = data.get("message", "").strip()
            if not user_msg:
                self.send_json({"error": "Empty message"}, status=400)
                return
            reply = BRAIN.chat(user_msg)
            self.send_json(reply)
            return

        # 2. Update Cali LLM Settings
        if path == "/api/cali/settings":
            BRAIN.update_llm_settings(data)
            self.send_json({"status": "success", "message": "Settings updated"})
            return

        # 3. Launch Module Process
        if path == "/api/module/launch":
            mod_id = data.get("id")
            res = HUB.launch_module_process(mod_id)
            self.send_json(res)
            return

        # 4. Proxmox & Fleet Updates Actions
        if path == "/api/proxmox/updates/check":
            res = PROXMOX.trigger_fleet_update_check()
            self.send_json(res)
            return

        if path == "/api/proxmox/updates/upgrade":
            vmid = int(data.get("vmid", 0))
            res = PROXMOX.upgrade_container(vmid)
            self.send_json(res)
            return

        if path == "/api/proxmox/container/action":
            vmid = int(data.get("vmid", 0))
            action = data.get("action", "")
            res = PROXMOX.container_action(vmid, action)
            self.send_json(res)
            return

        # Fallback: Check Referer for embedded module (/proxy/<port>/)
        referer = self.headers.get("Referer", "")
        if "/proxy/" in referer:
            ref_match = re.search(r"/proxy/(\d+)(?:/|$)", referer)
            if ref_match:
                target_port = int(ref_match.group(1))
                subpath = path
                if url.query:
                    subpath += "?" + url.query
                self._proxy_request("POST", target_port, subpath, data=raw_body)
                return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    preferred_port = CONFIG.get("server", {}).get("port", 8800)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    
    server = None
    candidate_ports = [preferred_port, 8788, 8789, 8880]
    for port in candidate_ports:
        try:
            server = ThreadingHTTPServer((host, port), CentralHubHandler)
            break
        except OSError as e:
            logger.warning(f"Port {port} unavailable ({e}), trying fallback...")

    if not server:
        logger.error("Could not bind to any candidate port! Exiting.")
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"  🌟 CALI MISSION CONTROL / CENTRAL COMMAND HUB       ")
    print(f"  Executive Dashboard: http://{host}:{port}           ")
    print(f"  Decoupled Multi-Department Fleet Observer           ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
