"""
client_auditor.py - Client Website Health Checker & Diagnostic Engine.
Adapted from Cali-Media's nexus_website_audit.py for client pitches,
pre-sales audits, and client website health assessments.
"""

import json
import logging
import re
import socket
import ssl
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("cali.health.auditor")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
AUDITS_HISTORY_FILE = DATA_DIR / "client_audits_history.json"


class ClientWebsiteAuditor:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def audit_url(self, target: str) -> Dict[str, Any]:
        """Runs a non-intrusive, passive diagnostic pass on any website."""
        raw_target = target.strip()
        if not raw_target.startswith("http://") and not raw_target.startswith("https://"):
            url = f"https://{raw_target}"
        else:
            url = raw_target

        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc or parsed.path
        if ":" in host:
            host = host.split(":")[0]

        t0 = time.time()
        findings = []
        score = 100

        # 1. DNS & Network Handshake
        dns_ok = False
        ip_addr = None
        try:
            ip_addr = socket.gethostbyname(host)
            dns_ok = True
        except Exception as e:
            findings.append({"category": "DNS", "severity": "critical", "issue": f"DNS resolution failed: {e}", "penalty": 40})
            score -= 40

        # 2. SSL/TLS Certificate Verification
        ssl_info = {"valid": False, "days_remaining": 0, "issuer": "Unknown", "subject": host}
        if dns_ok:
            try:
                ctx = ssl.create_default_context()
                with socket.create_connection((host, 443), timeout=4.0) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                        cert = ssock.getpeercert()
                        ssl_info["valid"] = True
                        
                        # Expiry calculation
                        not_after_str = cert.get("notAfter")
                        if not_after_str:
                            expire_dt = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                            now = datetime.now(timezone.utc)
                            days_left = (expire_dt - now).days
                            ssl_info["days_remaining"] = max(0, days_left)
                            ssl_info["expires_on"] = expire_dt.strftime("%Y-%m-%d")

                        # Issuer
                        issuer = dict(x[0] for x in cert.get("issuer", []))
                        ssl_info["issuer"] = issuer.get("organizationName") or issuer.get("commonName") or "Verified CA"

                        if ssl_info["days_remaining"] < 14:
                            findings.append({"category": "Security", "severity": "warning", "issue": f"SSL certificate expires in {ssl_info['days_remaining']} days.", "penalty": 10})
                            score -= 10
            except Exception as e:
                ssl_info["valid"] = False
                ssl_info["error"] = str(e)
                findings.append({"category": "Security", "severity": "high", "issue": f"SSL/TLS Handshake failed or untrusted: {e}", "penalty": 25})
                score -= 25

        # 3. HTTP Headers, Latency, and Content Analysis
        page_facts = {
            "title": "",
            "meta_description": "",
            "has_viewport": False,
            "has_canonical": False,
            "has_og_tags": False,
            "images_total": 0,
            "images_missing_alt": 0,
            "headers": {},
            "latency_ms": 0,
            "http_status": 0
        }

        try:
            req = urllib.request.Request(
                f"https://{host}",
                headers={"User-Agent": "Mozilla/5.0 (compatible; CaliMediaHealthCheck/1.0; +https://cali-media.ltd/audit)"}
            )
            fetch_t0 = time.time()
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                page_facts["latency_ms"] = round((time.time() - fetch_t0) * 1000)
                page_facts["http_status"] = resp.status
                headers_dict = dict(resp.headers)
                page_facts["headers"] = headers_dict

                # Check security headers
                lower_headers = {k.lower(): v for k, v in headers_dict.items()}
                sec_headers = {
                    "Strict-Transport-Security": "HSTS (Enforce HTTPS)",
                    "X-Content-Type-Options": "MIME-sniffing protection",
                    "X-Frame-Options": "Clickjacking defense",
                    "Content-Security-Policy": "Cross-site scripting defense",
                    "Referrer-Policy": "Privacy referrer leakage"
                }

                missing_sec = []
                for h_name, h_desc in sec_headers.items():
                    if h_name.lower() not in lower_headers:
                        missing_sec.append(h_name)

                if missing_sec:
                    penalty = min(20, len(missing_sec) * 4)
                    findings.append({
                        "category": "Security Headers",
                        "severity": "medium",
                        "issue": f"Missing {len(missing_sec)} recommended security headers ({', '.join(missing_sec[:3])}).",
                        "penalty": penalty
                    })
                    score -= penalty

                # Read body HTML (up to 200 KB)
                body = resp.read(200000).decode("utf-8", errors="ignore")

                # Title
                m_title = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
                if m_title:
                    page_facts["title"] = m_title.group(1).strip()
                else:
                    findings.append({"category": "SEO", "severity": "medium", "issue": "Missing HTML <title> tag.", "penalty": 10})
                    score -= 10

                # Meta description
                m_desc = re.search(r'<meta[^>]+name=[\'"]description[\'"][^>]+content=[\'"]([^\'"]*)[\'"]', body, re.IGNORECASE)
                if m_desc:
                    page_facts["meta_description"] = m_desc.group(1).strip()
                else:
                    findings.append({"category": "SEO", "severity": "low", "issue": "Missing meta description (search engines will auto-generate snippets).", "penalty": 5})
                    score -= 5

                # Viewport & OpenGraph
                page_facts["has_viewport"] = bool(re.search(r'<meta[^>]+name=[\'"]viewport[\'"]', body, re.IGNORECASE))
                if not page_facts["has_viewport"]:
                    findings.append({"category": "Mobile", "severity": "high", "issue": "No responsive viewport meta tag found.", "penalty": 15})
                    score -= 15

                page_facts["has_og_tags"] = bool(re.search(r'<meta[^>]+property=[\'"]og:', body, re.IGNORECASE))
                page_facts["has_canonical"] = bool(re.search(r'<link[^>]+rel=[\'"]canonical[\'"]', body, re.IGNORECASE))

                # Image alt inspection
                img_tags = re.findall(r'<img\s+[^>]*>', body, re.IGNORECASE)
                page_facts["images_total"] = len(img_tags)
                missing_alt = [img for img in img_tags if not re.search(r'\balt=[\'"][^\'"]*[\'"]', img, re.IGNORECASE)]
                page_facts["images_missing_alt"] = len(missing_alt)
                if page_facts["images_missing_alt"] > 0:
                    findings.append({
                        "category": "Accessibility & SEO",
                        "severity": "low",
                        "issue": f"{page_facts['images_missing_alt']} image(s) missing alt text.",
                        "penalty": min(8, page_facts["images_missing_alt"] * 2)
                    })
                    score -= min(8, page_facts["images_missing_alt"] * 2)

        except Exception as e:
            findings.append({"category": "HTTP", "severity": "high", "issue": f"Failed to retrieve homepage over HTTPS: {e}", "penalty": 30})
            score -= 30

        # Calculate Grade
        score = max(0, min(100, score))
        if score >= 90: grade = "A"
        elif score >= 80: grade = "B"
        elif score >= 65: grade = "C"
        elif score >= 50: grade = "D"
        else: grade = "F"

        # Construct Client Pitch Copy
        pitch = self._generate_client_pitch(host, grade, score, findings, page_facts, ssl_info)

        audit_record = {
            "id": f"aud-{int(time.time())}",
            "domain": host,
            "target_url": url,
            "ip_address": ip_addr,
            "grade": grade,
            "score": score,
            "ssl": ssl_info,
            "facts": page_facts,
            "findings": findings,
            "client_pitch": pitch,
            "audited_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_ms": round((time.time() - t0) * 1000)
        }

        self._save_to_history(audit_record)
        return audit_record

    def _generate_client_pitch(self, host: str, grade: str, score: int, findings: List[Dict], facts: Dict, ssl_info: Dict) -> str:
        """Constructs an executive, professional outreach pitch tailored to this client's site."""
        bullet_points = []
        for f in findings[:4]:
            bullet_points.append(f"• **{f['category']}:** {f['issue']}")

        issues_summary = "\n".join(bullet_points) if bullet_points else "• Site is generally healthy with minor optimization opportunities."

        return (
            f"Subject: Quick website health observation for {host}\n\n"
            f"Hi there,\n\n"
            f"I ran an automated health and security assessment on **{host}** through our agency diagnostic suite at Cali Media Ltd. "
            f"The site scored **{score}/100 (Grade {grade})**.\n\n"
            f"A few key items that may be impacting your search visibility and user security:\n"
            f"{issues_summary}\n\n"
            f"Our team handles full technical SEO, security header hardening, and web performance fixes. "
            f"Would you be open to a 5-minute chat this week on how we can implement these improvements for {host}?\n\n"
            f"Best regards,\n"
            f"Antony Brown\n"
            f"Cali Media Ltd (cali-media.ltd)"
        )

    def _save_to_history(self, record: Dict):
        history = self.load_history()
        history.insert(0, record)
        history = history[:50]  # keep 50
        AUDITS_HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")

    def load_history(self) -> List[Dict]:
        if AUDITS_HISTORY_FILE.exists():
            try:
                return json.loads(AUDITS_HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

