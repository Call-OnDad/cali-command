"""
token_extractor.py - Built-in Vibe & Brand Token Extractor for Cali Website Creator.
Extracts design tokens (colors, typography, radii, brand metadata, contact info)
from URLs or raw HTML/CSS without needing external MCP servers or heavy dependencies.
"""

import logging
import re
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

logger = logging.getLogger("cali.token_extractor")

# Standard UK Phone Regex Pattern
UK_PHONE_REGEX = re.compile(r'(?:(?:\+44\s?\(0\)\s?\d{2,5}|\+44\s?\d{2,5}|0\d{2,5})\s?\d{3,4}\s?\d{3,4})')

# Common Hex Color Regex
HEX_COLOR_REGEX = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')

# Font Family Regex
FONT_FAMILY_REGEX = re.compile(r'font-family\s*:\s*([^;!}\n]+)', re.IGNORECASE)

# Standard High-Converting Archetype Profiles
DESIGN_ARCHETYPES = {
    "bento-modern-saas": {
        "id": "bento-modern-saas",
        "name": "Bento Grid Modern SaaS",
        "subtitle": "Linear & Raycast Inspired · Glassmorphic Bento Layouts",
        "badge": "2026 TECH TREND",
        "theme_default": "electric-cyan",
        "keywords": ["tech", "software", "saas", "agency", "app", "cloud", "digital", "ai", "platform", "studio"],
        "features": [
            "Asymmetrical multi-card bento grid with subtle borders",
            "Radial glow backdrop lighting and glassmorphism",
            "Live interactive metric counters and telemetry badges",
            "High-contrast dark mode canvas with sleek micro-interactions"
        ]
    },
    "high-trust-trades": {
        "id": "high-trust-trades",
        "name": "High-Trust Emergency Trades",
        "subtitle": "UK Checkatrade & Gas Safe Standard · 45-Min Callout",
        "badge": "MAX CONVERSION",
        "theme_default": "trust-blue",
        "keywords": ["plumb", "boiler", "heat", "pipe", "roof", "electric", "locksmith", "drain", "handyman", "builder"],
        "features": [
            "Pinned 24/7 rapid emergency top banner with direct 1-tap dialing",
            "Thumb-friendly fixed mobile action dock with instant phone/WhatsApp quote",
            "Gas Safe & Which? Trusted Trader style dual-verification trust badges",
            "Transparent fixed-price diagnostic cards (Zero Callout Fee)"
        ]
    },
    "advocacy-fintech": {
        "id": "advocacy-fintech",
        "name": "Consumer Advocacy & Fintech",
        "subtitle": "Call-On Dad / Mom Standard · Martin Lewis Editorial Authority",
        "badge": "COMMUNITY TRUST",
        "theme_default": "warm-amber",
        "keywords": ["money", "finance", "bill", "tax", "council", "debt", "rights", "community", "budget", "pension"],
        "features": [
            "Official UK consumer rights notice & warning alert ribbons",
            "Dedicated £1.99 instant A4 print-off diagnostic download card",
            "Clear step-by-step diagnostic checklist & fair pricing benchmarks",
            "Verified non-profit standards and transparency statistics"
        ]
    },
    "luxury-boutique": {
        "id": "luxury-boutique",
        "name": "Luxury Boutique & Concierge",
        "subtitle": "High-End Dining, Automotive & Private Advisory",
        "badge": "PREMIUM EDITORIAL",
        "theme_default": "luxury-gold",
        "keywords": ["dining", "bistro", "restaurant", "auto", "detailing", "ceramic", "legal", "accounting", "luxury", "estate"],
        "features": [
            "Editorial serif headline typography paired with modern geometric sans",
            "Minimalist split hero section with generous architectural whitespace",
            "Concierge private reservation & consultation booking drawer",
            "Warm obsidian and burnished gold accent palette"
        ]
    },
    "vitality-health": {
        "id": "vitality-health",
        "name": "Clinical Health & Aesthetics",
        "subtitle": "CQC Dental, Dermatology & Wellness Standards",
        "badge": "PATIENT TRUST",
        "theme_default": "emerald",
        "keywords": ["dental", "implant", "teeth", "doctor", "clinic", "health", "physio", "aesthetic", "skin", "gym"],
        "features": [
            "Clean clinical emerald & soft mint trust architecture",
            "Before & after visual comparison cards with treatment timeline",
            "0% APR patient treatment finance calculator ribbon",
            "CQC registered provider accreditation badge and doctor profiles"
        ]
    }
}


def guess_archetype(text: str) -> str:
    """Classifies a business description or URL into the most effective 2026 design archetype."""
    text_lower = text.lower()
    for arch_id, data in DESIGN_ARCHETYPES.items():
        if any(kw in text_lower for kw in data["keywords"]):
            return arch_id
    return "high-trust-trades" # Safe default for UK services


def extract_tokens_from_html(html_text: str, base_url: str = "") -> Dict:
    """Parses raw HTML/CSS to extract brand colors, fonts, business name, and contact details."""
    result = {
        "url": base_url,
        "business_name": "",
        "city": "",
        "phone": "",
        "primary_color": "#38bdf8",
        "accent_color": "#0284c7",
        "bg_color": "#090d16",
        "font_family": "Plus Jakarta Sans",
        "recommended_archetype": "high-trust-trades",
        "colors_detected": [],
        "fonts_detected": []
    }

    if not html_text:
        return result

    # 1. Business Name Extraction
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.IGNORECASE | re.DOTALL)
    if title_match:
        raw_title = title_match.group(1).strip()
        # Clean title (split by |, -, •, —)
        parts = re.split(r'[\|\-â€¢â€”:]', raw_title)
        if parts:
            result["business_name"] = parts[0].strip()

    # Fallback to OG title
    if not result["business_name"]:
        og_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
        if og_match:
            result["business_name"] = og_match.group(1).strip()

    # 2. Phone Extraction
    phone_matches = UK_PHONE_REGEX.findall(html_text)
    if phone_matches:
        # Prefer numbers that look like direct UK landlines or mobiles
        valid_phones = [p.strip() for p in phone_matches if len(p.strip()) >= 10]
        if valid_phones:
            result["phone"] = valid_phones[0]

    # 3. Colors Extraction
    # Check meta theme-color
    meta_theme = re.search(r'<meta[^>]*name=["\']theme-color["\'][^>]*content=["\'](#[0-9a-fA-F]{3,6})["\']', html_text, re.IGNORECASE)
    if meta_theme:
        result["primary_color"] = meta_theme.group(1)

    all_hexes = HEX_COLOR_REGEX.findall(html_text)
    if all_hexes:
        # Tally frequencies
        freq: Dict[str, int] = {}
        for h in all_hexes:
            h_norm = f"#{h.upper()}"
            if h_norm not in ["#FFFFFF", "#000000", "#FFF", "#000"]:
                freq[h_norm] = freq.get(h_norm, 0) + 1
        
        sorted_colors = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        result["colors_detected"] = [c[0] for c in sorted_colors[:8]]
        if sorted_colors and not meta_theme:
            result["primary_color"] = sorted_colors[0][0]
            if len(sorted_colors) > 1:
                result["accent_color"] = sorted_colors[1][0]

    # 4. Font Extraction
    fonts_found = []
    # Check Google Fonts link
    for gf in re.finditer(r'fonts\.googleapis\.com/css2\?family=([^&"\']+)', html_text):
        family_param = gf.group(1)
        font_name = urllib.parse.unquote(family_param).split(':')[0].replace('+', ' ')
        fonts_found.append(font_name)

    # Check font-family styles
    for ff in FONT_FAMILY_REGEX.finditer(html_text):
        raw_font = ff.group(1).split(',')[0].strip(' "\'')
        if raw_font and raw_font.lower() not in ["inherit", "initial", "sans-serif", "serif", "monospace"]:
            fonts_found.append(raw_font)

    if fonts_found:
        result["fonts_detected"] = list(dict.fromkeys(fonts_found))[:5]
        result["font_family"] = result["fonts_detected"][0]

    # 5. City & Archetype Guessing
    uk_cities = [
        "London", "Birmingham", "Manchester", "Leeds", "Glasgow", "Sheffield",
        "Bristol", "Edinburgh", "Liverpool", "Surrey", "Kent", "Essex", "Cardiff",
        "Belfast", "Newcastle", "Nottingham", "Southampton", "Bath", "Oxford"
    ]
    for city in uk_cities:
        if re.search(r'\b' + city + r'\b', html_text, re.IGNORECASE):
            result["city"] = city
            break

    # Determine recommended archetype
    combined_content = f"{result['business_name']} {html_text[:2000]}"
    result["recommended_archetype"] = guess_archetype(combined_content)

    return result


def extract_tokens_from_url(url: str, timeout: float = 6.0) -> Dict:
    """Attempts to fetch live URL HTML to extract design tokens; falls back gracefully to domain heuristics."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    clean_domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
    domain_name = clean_domain.split('.')[0].replace('-', ' ').title()

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CaliDesignScanner/2.0"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            data = extract_tokens_from_html(content, base_url=url)
            if not data.get("business_name"):
                data["business_name"] = domain_name
            return data
    except Exception as e:
        logger.warning(f"Live URL fetch failed for {url} ({e}); generating intelligent archetype fallback.")
        # Intelligent heuristic fallback based on domain keywords
        archetype = guess_archetype(url)
        return {
            "url": url,
            "business_name": domain_name,
            "city": "London & Greater UK",
            "phone": "020 8123 4567",
            "primary_color": "#38bdf8" if archetype == "high-trust-trades" else ("#10b981" if archetype == "vitality-health" else "#f59e0b"),
            "accent_color": "#0284c7",
            "bg_color": "#090d16",
            "font_family": "Plus Jakarta Sans",
            "recommended_archetype": archetype,
            "colors_detected": ["#38BDF8", "#10B981", "#F59E0B"],
            "fonts_detected": ["Plus Jakarta Sans", "Inter"],
            "note": "Constructed from domain intelligence heuristic"
        }

