"""
domain_registry.py - Multi-domain management for Cali SEO & Search Radar.
Supports cali-media.ltd, call-on.media, .dad, .mom, .shop, and dynamically added domains.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("cali.seo.registry")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"
DOMAINS_FILE = DATA_DIR / "domains.json"


class DomainRegistry:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.domains: List[Dict] = []
        self.load()

    def load(self):
        """Loads domain list from persisted data/domains.json, falling back to config.json."""
        if DOMAINS_FILE.exists():
            try:
                self.domains = json.loads(DOMAINS_FILE.read_text(encoding="utf-8"))
                return
            except Exception as e:
                logger.error(f"Failed to read {DOMAINS_FILE}: {e}")

        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.domains = cfg.get("domains", [])
                self.save()
            except Exception as e:
                logger.error(f"Failed to read {CONFIG_FILE}: {e}")
                self.domains = []

    def save(self):
        """Persists the current domain list to data/domains.json."""
        DOMAINS_FILE.write_text(json.dumps(self.domains, indent=2), encoding="utf-8")

    def list_domains(self) -> List[Dict]:
        return self.domains

    def get_domain(self, domain_id: str) -> Optional[Dict]:
        for d in self.domains:
            if d.get("id") == domain_id or d.get("url") == domain_id:
                return d
        return None

    def add_domain(self, domain_data: Dict) -> Dict:
        domain_id = domain_data.get("id", "").strip().lower()
        if not domain_id:
            raw_url = domain_data.get("url", "").replace("https://", "").replace("http://", "").split("/")[0]
            domain_id = raw_url.lower()

        existing = self.get_domain(domain_id)
        if existing:
            existing.update(domain_data)
            self.save()
            return existing

        new_entry = {
            "id": domain_id,
            "url": domain_data.get("url", f"https://{domain_id}"),
            "name": domain_data.get("name", domain_id.capitalize()),
            "category": domain_data.get("category", "General Web"),
            "target_keywords": domain_data.get("target_keywords", []),
            "health_score": domain_data.get("health_score", 85),
            "last_crawled": domain_data.get("last_crawled", None)
        }
        self.domains.append(new_entry)
        self.save()
        return new_entry

    def remove_domain(self, domain_id: str) -> bool:
        before_len = len(self.domains)
        self.domains = [d for d in self.domains if d.get("id") != domain_id]
        if len(self.domains) != before_len:
            self.save()
            return True
        return False

    def update_keywords(self, domain_id: str, keywords: List[str]) -> bool:
        domain = self.get_domain(domain_id)
        if domain:
            domain["target_keywords"] = list(dict.fromkeys(keywords))
            self.save()
            return True
        return False
