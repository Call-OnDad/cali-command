"""
site_crawler.py - High-speed native HTTP crawler & on-page auditor.
Inspects titles, meta descriptions, OpenGraph, Twitter cards, canonical tags,
headings hierarchy, missing alt tags, and JSON-LD schema with zero external dependencies.
"""

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("cali.seo.crawler")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "crawls"


class SEOHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_desc = ""
        self.canonical = ""
        self.robots = ""
        self.og_tags = {}
        self.twitter_tags = {}
        self.h1_tags = []
        self.h2_tags = []
        self.h3_tags = []
        self.images_total = 0
        self.images_missing_alt = 0
        self.internal_links = []
        self.external_links = []
        self.has_json_ld = False
        self.json_ld_scripts = []

        # Parser state
        self._current_tag = None
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_h3 = False
        self._in_json_ld = False
        self._text_accumulator = []

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        attr_dict = {k.lower(): v for k, v in attrs if v is not None}

        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "h2":
            self._in_h2 = True
        elif tag == "h3":
            self._in_h3 = True
        elif tag == "link":
            rel = attr_dict.get("rel", "").lower()
            if rel == "canonical":
                self.canonical = attr_dict.get("href", "")
        elif tag == "meta":
            name = attr_dict.get("name", "").lower()
            prop = attr_dict.get("property", "").lower()
            content = attr_dict.get("content", "")

            if name == "description":
                self.meta_desc = content
            elif name == "robots":
                self.robots = content
            elif prop.startswith("og:"):
                self.og_tags[prop] = content
            elif name.startswith("twitter:"):
                self.twitter_tags[name] = content
        elif tag == "img":
            self.images_total += 1
            alt = attr_dict.get("alt")
            if alt is None or not alt.strip():
                self.images_missing_alt += 1
        elif tag == "a":
            href = attr_dict.get("href", "")
            if href:
                if href.startswith("http://") or href.startswith("https://"):
                    self.external_links.append(href)
                elif not href.startswith("#") and not href.startswith("mailto:"):
                    self.internal_links.append(href)
        elif tag == "script":
            script_type = attr_dict.get("type", "").lower()
            if "application/ld+json" in script_type:
                self.has_json_ld = True
                self._in_json_ld = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "h3":
            self._in_h3 = False
        elif tag == "script":
            self._in_json_ld = False
        self._current_tag = None

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return

        if self._in_title:
            self.title += text
        elif self._in_h1:
            self.h1_tags.append(text)
        elif self._in_h2:
            self.h2_tags.append(text)
        elif self._in_h3:
            self.h3_tags.append(text)
        elif self._in_json_ld:
            self.json_ld_scripts.append(text)

        if self._current_tag not in ("script", "style"):
            self._text_accumulator.append(text)

    def get_body_text(self) -> str:
        return " ".join(self._text_accumulator)


class SiteCrawler:
    def __init__(self, user_agent: str = None):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; Cali-SEO-Radar/1.0; +https://cali-media.ltd)"

    def crawl_url(self, target_url: str) -> Dict:
        """Crawls a single URL, measures latency, extracts on-page signals and computes health score."""
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = f"https://{target_url}"

        parsed_domain = urllib.parse.urlparse(target_url).netloc
        start_time = time.time()

        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                status_code = response.getcode()
                latency_ms = round((time.time() - start_time) * 1000)
                charset = response.headers.get_content_charset() or "utf-8"
                html_bytes = response.read(500000)  # Read up to 500KB
                html_text = html_bytes.decode(charset, errors="replace")
                final_url = response.geturl()
        except urllib.error.HTTPError as e:
            return self._build_error_report(target_url, parsed_domain, e.code, f"HTTP Error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            return self._build_error_report(target_url, parsed_domain, 0, f"Connection Failed: {e.reason}")
        except Exception as e:
            return self._build_error_report(target_url, parsed_domain, 0, f"Crawl Error: {str(e)}")

        parser = SEOHTMLParser()
        try:
            parser.feed(html_text)
        except Exception as e:
            logger.warning(f"HTML parsing notice for {target_url}: {e}")

        body_text = parser.get_body_text()
        words = body_text.split()
        word_count = len(words)

        # Health Score Assessment
        score = 100
        issues = []
        recommendations = []

        # 1. Title Audit
        title_len = len(parser.title)
        if not parser.title:
            score -= 20
            issues.append({"type": "critical", "msg": "Missing <title> tag"})
            recommendations.append("Add a descriptive page title (50-60 characters) containing your primary target keyword.")
        elif title_len < 30:
            score -= 5
            issues.append({"type": "warning", "msg": f"Title tag too short ({title_len} chars)"})
            recommendations.append("Expand page title to at least 45-60 characters for maximum SERP click-through.")
        elif title_len > 65:
            score -= 5
            issues.append({"type": "warning", "msg": f"Title tag exceeds Google SERP limit ({title_len} chars)"})
            recommendations.append("Shorten title tag to under 60 characters to prevent Google truncation in search results.")

        # 2. Meta Description Audit
        desc_len = len(parser.meta_desc)
        if not parser.meta_desc:
            score -= 15
            issues.append({"type": "critical", "msg": "Missing meta description"})
            recommendations.append("Provide a compelling meta description (120-155 characters) with a clear call to action.")
        elif desc_len < 70:
            score -= 5
            issues.append({"type": "warning", "msg": f"Meta description is short ({desc_len} chars)"})
        elif desc_len > 165:
            score -= 5
            issues.append({"type": "warning", "msg": f"Meta description is long ({desc_len} chars)"})

        # 3. Headings Hierarchy
        if len(parser.h1_tags) == 0:
            score -= 10
            issues.append({"type": "critical", "msg": "No H1 heading found on page"})
            recommendations.append("Include exactly one primary H1 heading containing the main topic keyword.")
        elif len(parser.h1_tags) > 1:
            score -= 5
            issues.append({"type": "warning", "msg": f"Multiple H1 headings detected ({len(parser.h1_tags)})"})
            recommendations.append("Maintain a clean single H1 heading per page, using H2/H3 for subsections.")

        # 4. Canonical Link
        if not parser.canonical:
            score -= 10
            issues.append({"type": "warning", "msg": "Missing self-referencing rel='canonical' link"})
            recommendations.append("Specify rel='canonical' tag to prevent duplicate content indexation.")

        # 5. Image Alt Attributes
        if parser.images_missing_alt > 0:
            score -= min(10, parser.images_missing_alt * 2)
            issues.append({"type": "warning", "msg": f"{parser.images_missing_alt} image(s) missing alt attributes"})
            recommendations.append(f"Add descriptive alt text to all {parser.images_missing_alt} images for Google Images search.")

        # 6. Structured Data
        if not parser.has_json_ld:
            score -= 5
            issues.append({"type": "info", "msg": "No Schema.org JSON-LD structured data detected"})
            recommendations.append("Implement Schema.org JSON-LD (e.g. Organization, Article, Product) for rich snippets.")

        # 7. Speed / Latency
        if latency_ms > 1200:
            score -= 10
            issues.append({"type": "warning", "msg": f"Slow server response time ({latency_ms}ms)"})
            recommendations.append("Enable page caching or optimize backend response time to sub-400ms.")

        score = max(10, min(100, score))

        report = {
            "status": "success",
            "url": target_url,
            "final_url": final_url,
            "domain": parsed_domain,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "health_score": score,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "seo": {
                "title": parser.title,
                "title_length": title_len,
                "meta_description": parser.meta_desc,
                "meta_description_length": desc_len,
                "canonical": parser.canonical,
                "robots_directive": parser.robots or "index, follow",
                "h1": parser.h1_tags,
                "h2_count": len(parser.h2_tags),
                "h3_count": len(parser.h3_tags),
                "word_count": word_count,
                "estimated_read_time_min": max(1, round(word_count / 220)),
                "images_total": parser.images_total,
                "images_missing_alt": parser.images_missing_alt,
                "internal_links_count": len(parser.internal_links),
                "external_links_count": len(parser.external_links),
                "has_schema_json_ld": parser.has_json_ld,
                "og_tags": parser.og_tags,
                "twitter_tags": parser.twitter_tags
            },
            "issues": issues,
            "recommendations": recommendations
        }

        # Save to disk
        cache_file = DATA_DIR / f"{parsed_domain.replace(':', '_')}.json"
        try:
            cache_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to cache crawl report: {e}")

        return report

    def _build_error_report(self, url: str, domain: str, code: int, reason: str) -> Dict:
        return {
            "status": "error",
            "url": url,
            "domain": domain,
            "status_code": code,
            "latency_ms": 0,
            "health_score": 0,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "issues": [{"type": "critical", "msg": reason}],
            "recommendations": ["Check DNS settings, web server status, and domain connectivity."],
            "seo": {
                "title": "",
                "meta_description": "",
                "canonical": "",
                "word_count": 0,
                "images_total": 0,
                "images_missing_alt": 0,
                "has_schema_json_ld": False
            }
        }

    def load_cached_report(self, domain_id: str) -> Optional[Dict]:
        clean_id = domain_id.replace("https://", "").replace("http://", "").split("/")[0]
        cache_file = DATA_DIR / f"{clean_id}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None
