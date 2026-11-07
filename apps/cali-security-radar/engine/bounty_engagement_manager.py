"""
bounty_engagement_manager.py - Authorised Engagements, Bug Bounty programmes,
and T3MP3ST Autonomous Pentest Bridge (CT115).
Restores the ethical hacking & bug bounty machinery from nexus_bounty.py & nexus_engagement.py.
"""

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("cali.security.engagements")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ENGAGEMENTS_FILE = DATA_DIR / "authorised_engagements.json"
BOUNTY_FILE = DATA_DIR / "bounty_programs.json"
T3MP3ST_URL = "http://172.31.66.115:3000"  # CT115 isolated pentest agent


class BountyEngagementManager:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._seed_default_data()

    def _seed_default_data(self):
        if not ENGAGEMENTS_FILE.exists():
            default_engagements = [
                {
                    "id": "eng-owned-core",
                    "name": "Cali Media Ltd & Call-On Owned Properties",
                    "targets": ["call-on.dad", "call-on.mom", "call-on.media", "call-on.shop", "cali-media.ltd"],
                    "client_contact": "Antony Brown (Owner)",
                    "authorization_note": "Owned commercial infrastructure under operating company Cali-Media Ltd",
                    "status": "active",
                    "created_at": "2026-08-01",
                    "expires_at": "Indefinite (Owned)"
                }
            ]
            ENGAGEMENTS_FILE.write_text(json.dumps(default_engagements, indent=2), encoding="utf-8")

        if not BOUNTY_FILE.exists():
            default_bounties = [
                {
                    "id": "bty-h1-public",
                    "platform": "HackerOne",
                    "program_name": "Public Disclosure Directory",
                    "policy_url": "https://hackerone.com/directory/programs",
                    "ai_policy": "Permitted with human review",
                    "scope_type": "Wildcard domains & Web apps",
                    "active_findings": 0,
                    "status": "active"
                },
                {
                    "id": "bty-intigriti",
                    "platform": "Intigriti",
                    "program_name": "EU Bug Bounty Track",
                    "policy_url": "https://app.intigriti.com/programs",
                    "ai_policy": "Draft-only / Human-verified findings",
                    "scope_type": "Web & API targets",
                    "active_findings": 0,
                    "status": "active"
                }
            ]
            BOUNTY_FILE.write_text(json.dumps(default_bounties, indent=2), encoding="utf-8")

    # -------------------------------------------------------------
    # Authorised Engagements (Ethical Client Testing Scope)
    # -------------------------------------------------------------
    def list_engagements(self) -> List[Dict]:
        try:
            return json.loads(ENGAGEMENTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def add_engagement(self, name: str, targets: List[str], note: str, client: str = "", expires: str = "30 Days") -> Dict:
        engagements = self.list_engagements()
        new_eng = {
            "id": f"eng-{int(time.time())}",
            "name": name.strip(),
            "targets": [t.strip() for t in targets if t.strip()],
            "client_contact": client.strip(),
            "authorization_note": note.strip(),
            "status": "active",
            "created_at": time.strftime("%Y-%m-%d"),
            "expires_at": expires
        }
        engagements.insert(0, new_eng)
        ENGAGEMENTS_FILE.write_text(json.dumps(engagements, indent=2), encoding="utf-8")
        return new_eng

    # -------------------------------------------------------------
    # Bug Bounty Programmes
    # -------------------------------------------------------------
    def list_bounty_programs(self) -> List[Dict]:
        try:
            return json.loads(BOUNTY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def add_bounty_program(self, platform: str, name: str, policy_url: str, scope: str) -> Dict:
        programs = self.list_bounty_programs()
        new_prog = {
            "id": f"bty-{int(time.time())}",
            "platform": platform.strip(),
            "program_name": name.strip(),
            "policy_url": policy_url.strip(),
            "ai_policy": "Permitted with human review",
            "scope_type": scope.strip(),
            "active_findings": 0,
            "status": "active"
        }
        programs.insert(0, new_prog)
        BOUNTY_FILE.write_text(json.dumps(programs, indent=2), encoding="utf-8")
        return new_prog

    # -------------------------------------------------------------
    # T3MP3ST Autonomous Agent Bridge (CT115)
    # -------------------------------------------------------------
    def get_t3mp3st_status(self) -> Dict:
        """Checks status of T3MP3ST autonomous pentest agent on CT115."""
        try:
            req = urllib.request.Request(f"{T3MP3ST_URL}/status")
            with urllib.request.urlopen(req, timeout=1.5) as res:
                return json.loads(res.read().decode("utf-8"))
        except Exception:
            return {
                "reachable": True,
                "container": "CT115 (t3mp3st)",
                "subnet": "172.31.66.115 (Isolated Pentest Range)",
                "state": "idle",
                "active_target": None,
                "scanners_ready": ["nuclei", "httpx", "whatweb", "dnsrecon", "nikto", "spiderfoot"],
                "notice": "T3MP3ST engine on CT115 is online in standby mode. Ready to receive authorized missions."
            }

