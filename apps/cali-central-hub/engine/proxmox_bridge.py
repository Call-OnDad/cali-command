"""
Cali Mission Control -- Proxmox & Homelab Infrastructure Bridge
Connects directly to CT117 (AHAS API at http://192.168.0.60:5000) and Proxmox Host (192.168.0.10:8006).
Provides real-time container metrics, apt package update scanning, PBS backups, and container power controls.
"""

import json
import logging
import ssl
import time
import urllib.request
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CaliProxmoxBridge")

CT117_BASE = "http://192.168.0.60:5000"
PROXMOX_HOST = "https://192.168.0.10:8006/api2/json"
PROXMOX_TOKEN = "PVEAPIToken=cali-agent@pve!dashboard=5a17ceb1-edb6-46bb-8b50-4f8c6156298a"

# Friendly names for all known fleet containers & VMs
CONTAINER_ROLES = {
    "100": {"name": "Umami Analytics", "category": "Analytics & Traffic"},
    "101": {"name": "Media Stack (Plex)", "category": "Media & Entertainment"},
    "102": {"name": "MariaDB Database", "category": "Core Database"},
    "103": {"name": "Recyclarr", "category": "Media Automation"},
    "104": {"name": "Node.js Signaling", "category": "Web & WebRTC"},
    "105": {"name": "Pi-hole DNS", "category": "Network & DNS"},
    "106": {"name": "Firefly III", "category": "Finance & Accounting"},
    "107": {"name": "Proxmox Backup Server", "category": "Storage & Backups"},
    "108": {"name": "Uptime Kuma", "category": "Uptime Monitoring"},
    "109": {"name": "CrowdSec IPS", "category": "Security & Defense"},
    "110": {"name": "OnlyOffice Docs", "category": "Productivity & Office"},
    "111": {"name": "Vaultwarden", "category": "Security & Vault"},
    "112": {"name": "Home Assistant OS", "category": "Smart Home & IoT"},
    "113": {"name": "Prometheus Metrics", "category": "Observability"},
    "114": {"name": "Loki Logs", "category": "Logging & Auditing"},
    "115": {"name": "T3MP3ST Pentest Agent", "category": "Security & Bug Bounty"},
    "116": {"name": "Kima Hub", "category": "Integration"},
    "117": {"name": "AHAS Cali Brain", "category": "Executive AI Hub"},
    "118": {"name": "Revive Adserver", "category": "Marketing & Ads"},
    "119": {"name": "Local LLM Server", "category": "AI Inference"},
    "120": {"name": "SerpBear SEO", "category": "Search & SEO"},
    "121": {"name": "Spiderfoot OSINT", "category": "Reconnaissance"},
    "122": {"name": "Playwright Automation", "category": "Browser Worker"},
    "123": {"name": "Jev Trader", "category": "Trading & Markets"},
    "124": {"name": "Nexus Security", "category": "Security & Defense"},
    "125": {"name": "Helm Sandbox", "category": "Testing & Lab"},
    "126": {"name": "Helm Control", "category": "Deployment"},
    "127": {"name": "Cali Video Studio", "category": "Video & Content"},
    "130": {"name": "Vision Bridge", "category": "Computer Vision"},
    "140": {"name": "Cali Demo", "category": "Demonstration"},
    "141": {"name": "Vuln Range", "category": "Security Lab"},
    "500": {"name": "Caddy Reverse Proxy", "category": "Edge & Web Host"}
}


class ProxmoxBridge:
    def __init__(self, ct117_url: str = CT117_BASE):
        self.base_url = ct117_url
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

    def _http_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, timeout: float = 6.0) -> Any:
        url = f"{self.base_url}{endpoint}"
        body = json.dumps(data).encode("utf-8") if data else None
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                return json.loads(res.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"CT117 API request {method} {endpoint} failed: {e}")
            return {"error": str(e)}

    # 1. Fleet Updates (Apt Package Status across all LXC containers)
    def get_fleet_updates(self) -> Dict[str, Any]:
        """Gets live status of pending package updates across all fleet containers."""
        res = self._http_request("/api/fleet-updates", timeout=5.0)
        if isinstance(res, dict) and "containers" in res:
            containers = res.get("containers", [])
            upgradable_total = sum(c.get("upgradable_count", 0) or 0 for c in containers)
            containers_with_updates = [c for c in containers if (c.get("upgradable_count") or 0) > 0]
            return {
                "ok": True,
                "checking": res.get("checking", False),
                "total_containers_checked": len(containers),
                "upgradable_packages_total": upgradable_total,
                "containers_with_updates_count": len(containers_with_updates),
                "containers_with_updates": containers_with_updates,
                "all_containers": containers
            }
        return {"ok": False, "error": str(res.get("error", "Failed to fetch fleet updates")), "containers_with_updates": []}

    def trigger_fleet_update_check(self) -> Dict[str, Any]:
        """Triggers a fleet-wide apt update check in the background."""
        return self._http_request("/api/fleet-updates/check", method="POST", timeout=5.0)

    def upgrade_container(self, vmid: int) -> Dict[str, Any]:
        """Executes apt upgrade on a specific container."""
        return self._http_request(f"/api/fleet-updates/{vmid}/upgrade", method="POST", timeout=8.0)

    # 2. Container Stats (Live CPU, RAM, Disk, Uptime for all 32 containers)
    def get_container_stats(self) -> List[Dict[str, Any]]:
        """Retrieves real-time CPU, RAM, Disk, and status for all containers, with direct Proxmox fallback."""
        res = self._http_request("/api/proxmox/container_stats", timeout=6.0)
        containers = []
        if isinstance(res, dict) and "data" in res and "containers" in res["data"]:
            raw_cts = res["data"]["containers"]
            for c in raw_cts:
                ctid = str(c.get("ctid", ""))
                role_info = CONTAINER_ROLES.get(ctid, {})
                c["friendly_name"] = role_info.get("name", c.get("name", f"CT{ctid}"))
                c["category"] = role_info.get("category", "General Homelab")
                containers.append(c)
            return sorted(containers, key=lambda x: int(x.get("ctid", 0)))

        # Direct Proxmox API fallback (ultra-fast, ~1s)
        try:
            req = urllib.request.Request(f"{PROXMOX_HOST}/nodes/pve/lxc", headers={"Authorization": PROXMOX_TOKEN})
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=6.0) as px_res:
                px_data = json.loads(px_res.read().decode("utf-8")).get("data", [])
                for ct in px_data:
                    vmid = str(ct.get("vmid", ""))
                    role_info = CONTAINER_ROLES.get(vmid, {})
                    mem = ct.get("mem", 0)
                    maxmem = ct.get("maxmem", 1) or 1
                    disk = ct.get("disk", 0)
                    maxdisk = ct.get("maxdisk", 1) or 1
                    containers.append({
                        "ctid": int(vmid),
                        "name": ct.get("name", f"CT{vmid}"),
                        "friendly_name": role_info.get("name", ct.get("name", f"CT{vmid}")),
                        "category": role_info.get("category", "General Homelab"),
                        "status": ct.get("status", "unknown"),
                        "cpu_pct": round(ct.get("cpu", 0) * 100, 1),
                        "mem_mb": round(mem / (1024 * 1024), 0),
                        "max_mem_mb": round(maxmem / (1024 * 1024), 0),
                        "mem_pct": round((mem / maxmem) * 100, 1),
                        "disk_gb": round(disk / (1024 ** 3), 1),
                        "max_disk_gb": round(maxdisk / (1024 ** 3), 1),
                        "disk_pct": round((disk / maxdisk) * 100, 1),
                        "uptime_s": ct.get("uptime", 0)
                    })
        except Exception as px_err:
            logger.warning(f"Direct Proxmox LXC query failed: {px_err}")

        return sorted(containers, key=lambda x: int(x.get("ctid", 0)))

    # 3. Host Raw Metrics (Intel Xeon E5-2620 Vitals)
    def get_host_vitals(self) -> Dict[str, Any]:
        """Gets CPU load, RAM usage, and cores directly from Proxmox host."""
        res = self._http_request("/api/proxmox/host_raw", timeout=5.0)
        if isinstance(res, dict) and "cpu_pct" in res:
            return res
        # Direct fallback to Proxmox API if CT117 endpoint returned an error
        try:
            req = urllib.request.Request(f"{PROXMOX_HOST}/nodes/pve/status", headers={"Authorization": PROXMOX_TOKEN})
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=4.0) as px_res:
                px_data = json.loads(px_res.read().decode("utf-8")).get("data", {})
                mem = px_data.get("memory", {})
                return {
                    "cpu_pct": round(px_data.get("cpu", 0) * 100, 1),
                    "load1": float(px_data.get("loadavg", [0, 0, 0])[0]),
                    "load5": float(px_data.get("loadavg", [0, 0, 0])[1]),
                    "load15": float(px_data.get("loadavg", [0, 0, 0])[2]),
                    "mem_used": mem.get("used", 0),
                    "mem_total": mem.get("total", 0),
                    "mem_pct": round((mem.get("used", 0) / mem.get("total", 1)) * 100, 1),
                    "model": px_data.get("cpuinfo", {}).get("model", "Intel Xeon E5-2620"),
                    "cpus": px_data.get("cpuinfo", {}).get("cpus", 12)
                }
        except Exception as px_err:
            return {"error": str(px_err), "cpu_pct": 0, "load1": 0}

    # 4. Container Power Actions (Start, Stop, Shutdown, Reboot)
    def container_action(self, vmid: int, action: str) -> Dict[str, Any]:
        """Runs start/stop/shutdown/reboot on a container."""
        if action not in ("start", "stop", "shutdown", "reboot"):
            return {"ok": False, "error": f"Invalid action: {action}"}
        return self._http_request(f"/api/proxmox/container/{vmid}/action", method="POST", data={"action": action}, timeout=8.0)

    # 5. Backups & PBS Datastore Status
    def get_backup_status(self) -> Dict[str, Any]:
        """Fetches backup jobs and PBS datastore snapshots."""
        res = self._http_request("/api/backups/status", timeout=5.0)
        if isinstance(res, dict) and "jobs" in res:
            return res
        return {"jobs": [], "groups": []}

    # 6. Pulse Monitored Homelab Services
    def get_pulse_services(self) -> Dict[str, Any]:
        """Returns online/offline state of all core homelab services."""
        res = self._http_request("/api/pulse/status", timeout=5.0)
        if isinstance(res, dict) and not res.get("error"):
            return res
        return {}

    # 7. Unified Full Fleet Overwatch (Combines everything for Central Hub UI & Cali)
    def get_full_overwatch(self) -> Dict[str, Any]:
        """Unified snapshot of host vitals, 32 containers, pending updates, backups, and services."""
        host = self.get_host_vitals()
        containers = self.get_container_stats()
        updates = self.get_fleet_updates()
        backups = self.get_backup_status()
        pulse = self.get_pulse_services()

        running_count = sum(1 for c in containers if c.get("status") == "running")
        stopped_count = sum(1 for c in containers if c.get("status") != "running")

        # Map pending update count into container objects
        update_map = {c.get("vmid"): c for c in updates.get("all_containers", [])}
        for c in containers:
            vmid = c.get("ctid")
            u_info = update_map.get(vmid, {})
            c["upgradable_count"] = u_info.get("upgradable_count", 0)
            c["update_status"] = u_info.get("status", "unknown")
            c["packages"] = u_info.get("packages", "")

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "host": host,
            "containers_count": len(containers),
            "running_count": running_count,
            "stopped_count": stopped_count,
            "updates_summary": {
                "checking": updates.get("checking", False),
                "upgradable_total": updates.get("upgradable_packages_total", 0),
                "containers_with_updates_count": updates.get("containers_with_updates_count", 0),
                "flagged_containers": updates.get("containers_with_updates", [])
            },
            "backups_summary": {
                "recent_jobs_count": len(backups.get("jobs", [])),
                "pbs_groups_count": len(backups.get("groups", []))
            },
            "services_summary": {
                "total": len(pulse),
                "online": sum(1 for s in pulse.values() if s.get("up")),
                "offline": sum(1 for s in pulse.values() if not s.get("up"))
            },
            "containers": containers,
            "pulse_services": pulse
        }


# Singleton instance
PROXMOX = ProxmoxBridge()
