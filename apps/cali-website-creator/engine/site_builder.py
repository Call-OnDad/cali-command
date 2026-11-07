"""
site_builder.py - 2026 Design Vault Archetype Construction Engine, Vibe Matcher & Pitch Generator.
Enables rapid prototyping of bespoke, high-converting client websites and modern 2026 UI architectures.
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from engine.token_extractor import DESIGN_ARCHETYPES, guess_archetype

logger = logging.getLogger("cali.site_builder")

CLIENT_TEMPLATES = [
    {
        "id": "client-emergency-trades",
        "niche": "Local Trades & Home Services",
        "business_name": "Apex Emergency Plumbing & Heating",
        "city": "London & Greater Surrey",
        "archetype": "high-trust-trades",
        "theme": "trust-blue",
        "phone": "020 8123 4567",
        "rating": "4.9 ★★★★★ on Checkatrade & Google (210+ reviews)",
        "headline": "24/7 Rapid Emergency Plumbing & Boiler Specialists",
        "subhead": "Gas Safe registered engineers arriving in under 45 minutes across London & Surrey. Transparent fixed pricing, zero callout fees.",
        "primary_cta": "Call Now: 020 8123 4567",
        "secondary_cta": "Get Instant Quote",
        "domain_target": "apex-plumbing.call-on.media",
        "services": [
            {"title": "Emergency Boiler Repair", "desc": "Same-day diagnostics and repairs for all major brands with genuine OEM parts.", "price": "From £85 fixed"},
            {"title": "Blocked Drains & Leak Detection", "desc": "Advanced thermal & CCTV acoustic trace to pinpoint hidden leaks without destruction.", "price": "From £70 fixed"},
            {"title": "Full Central Heating Installation", "desc": "Energy-efficient condensing boilers with 10-year manufacturer warranty.", "price": "Free Survey"}
        ],
        "testimonial": {
            "quote": "Apex saved our heating on a freezing Sunday morning within 40 minutes of calling. Polite, clean, and upfront about cost.",
            "author": "Mark S. · Homeowner in Wimbledon"
        }
    },
    {
        "id": "client-modern-saas",
        "niche": "Technology, Cloud & SaaS",
        "business_name": "Aetheria Cloud Telemetry & AI",
        "city": "London Tech City",
        "archetype": "bento-modern-saas",
        "theme": "electric-cyan",
        "phone": "020 7946 0882",
        "rating": "99.99% Uptime Verified · SOC2 Type II Certified",
        "headline": "Sovereign Observability & Real-Time Event Streaming",
        "subhead": "Sub-millisecond latency telemetry with automated anomaly detection, zero cold starts, and native MCP agent connectors.",
        "primary_cta": "Start Free 14-Day Trial",
        "secondary_cta": "Explore Live API Docs",
        "domain_target": "aetheria-cloud.call-on.media",
        "services": [
            {"title": "Distributed Event Engine", "desc": "Process 100,000+ events per second with zero-loss durability and instant failover.", "price": "99.99% SLA"},
            {"title": "Agentic MCP Bridge", "desc": "Native bidirectional Model Context Protocol sockets for autonomous coding agents.", "price": "Plug & Play"},
            {"title": "Edge Security Shield", "desc": "Automated DDoS mitigation, WAF rule synthesis, and sovereign EU/UK data residency.", "price": "Included"}
        ],
        "testimonial": {
            "quote": "Aetheria replaced three legacy monitoring tools and cut our infrastructure alert noise by 80% on day one.",
            "author": "Elena V. · VP of Engineering, FinTech Scaleup"
        }
    },
    {
        "id": "client-advocacy-rights",
        "niche": "Consumer Rights & Household Advice",
        "business_name": "Call-On Dad Emergency Action Network",
        "city": "Nationwide UK",
        "archetype": "advocacy-fintech",
        "theme": "warm-amber",
        "phone": "0800 123 4567",
        "rating": "Verified Non-Profit Standards · Free Public Service",
        "headline": "Stop Rogue Tradesmen & Unfair Utility Direct Debits",
        "subhead": "Practical, step-by-step diagnostic checklists and fair UK pricing benchmarks to protect UK families from emergency fees.",
        "primary_cta": "Download £1.99 A4 Checklist",
        "secondary_cta": "Browse Free Community Guides",
        "domain_target": "call-on.dad",
        "services": [
            {"title": "Boiler & Heating Reset Walkthrough", "desc": "60-second condensation pipe thaw and pressure loop diagnostic before paying an engineer.", "price": "£1.99 Toolkit"},
            {"title": "Direct Debit Dispute Letter", "desc": "Statutory template letter citing Ofgem regulations to force energy suppliers to refund credit.", "price": "Free Download"},
            {"title": "Fair UK Trades Price Checker", "desc": "Real regional price ranges for plumbing, electrical, and roofing callouts.", "price": "Free Checker"}
        ],
        "testimonial": {
            "quote": "Call-On Dad saved my mum £280 by showing her how to reset her Worcester boiler pressure with a £2 valve key. Essential advice.",
            "author": "Sarah T. · Leeds"
        }
    },
    {
        "id": "client-restaurant-dining",
        "niche": "Restaurants & Hospitality",
        "business_name": "The Copper Kettle Artisan Bistro",
        "city": "Bath, Somerset",
        "archetype": "luxury-boutique",
        "theme": "luxury-gold",
        "phone": "01225 987 654",
        "rating": "4.8 ★★★★★ on OpenTable & TripAdvisor (340+ reviews)",
        "headline": "Locally Sourced Seasonal Dining & Handcrafted Cellar",
        "subhead": "Woodfired artisan sourdough, Somerset dry-aged steaks, and organic West Country cellar pairings.",
        "primary_cta": "Reserve a Table Online",
        "secondary_cta": "View Seasonal Menu",
        "domain_target": "copper-kettle.call-on.media",
        "services": [
            {"title": "Chef's Tasting Menu", "desc": "5-course culinary journey celebrating seasonal West Country produce.", "price": "£55 per guest"},
            {"title": "Sunday Woodfired Roasts", "desc": "Slow-cooked Somerset sirloin with beef dripping potatoes and giant Yorkshire puddings.", "price": "From £19.50"},
            {"title": "Private Dining & Garden Room", "desc": "Exclusive hire of our mezzanine garden room for celebrations and corporate dinners.", "price": "Enquire Online"}
        ],
        "testimonial": {
            "quote": "Easily the best dining experience in Bath. The steak was unbelievable and the cocktail pairing was masterclass level.",
            "author": "Chloe & Liam D. · Food & Travel Critics"
        }
    },
    {
        "id": "client-dental-health",
        "niche": "Health, Dental & Aesthetics",
        "business_name": "Kingsway Specialist Dental & Implants",
        "city": "Manchester City Centre",
        "archetype": "vitality-health",
        "theme": "emerald",
        "phone": "0161 876 5432",
        "rating": "5.0 ★★★★★ on Google & CQC Certified (480+ patient reviews)",
        "headline": "Transforming Smiles with Gentle, Modern Dentistry",
        "subhead": "Invisalign diamond providers, painless single-visit dental implants, and 0% APR treatment finance in Manchester.",
        "primary_cta": "Book Free Consultation",
        "secondary_cta": "Explore Treatments",
        "domain_target": "kingsway-dental.call-on.media",
        "services": [
            {"title": "Invisalign Clear Aligners", "desc": "Discreet, removable teeth straightening with 3D iTero digital preview.", "price": "From £28/month"},
            {"title": "Single-Tooth & Full Implants", "desc": "Permanent, natural-looking replacement roots placed under gentle IV sedation.", "price": "Free Assessment"},
            {"title": "Enlighten Teeth Whitening", "desc": "Guaranteed B1 shade brighten system with zero sensitivity formula.", "price": "£395 all-inclusive"}
        ],
        "testimonial": {
            "quote": "I was terrified of the dentist for 10 years until I met Dr. Sarah at Kingsway. The IV sedation made my implant completely painless.",
            "author": "James R. · Didsbury, Manchester"
        }
    }
]

class SiteBuilder:
    def __init__(self, config: Dict):
        self.config = config
        self.export_dir = Path(config.get("export_dir", "d:/The Cali Project/apps/cali-website-creator/exports"))
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[Dict]:
        return CLIENT_TEMPLATES

    def list_archetypes(self) -> Dict:
        return DESIGN_ARCHETYPES

    def generate_pitch(self, business_name: str, niche: str, city: str, site_url: str, phone: str = "") -> Dict:
        """Generates ready-to-send cold outreach copy (Email, DM, and Phone Script)."""
        slug = re.sub(r'[^a-zA-Z0-9]', '', business_name.lower())[:15]
        preview_link = site_url if site_url.startswith("http") else f"https://{site_url}"

        email_subject = f"Quick question regarding {business_name}'s mobile website"
        email_body = f"""Hi {business_name} team,

I came across your business while researching top {niche} providers in {city}.

I noticed your current website has a few mobile layout and loading friction points that might be costing you calls and quote inquiries when customers search on their phones.

Rather than just talking about it, my studio (Cali Media Ltd) went ahead and built an interactive, modern mobile mockup specifically tailored for {business_name}:

👉 Preview the Live Mockup: {preview_link}

Key upgrades we included in this prototype:
• One-tap phone calling and WhatsApp quote booking
• Lightning-fast 100% mobile responsive layout
• Dedicated services grid highlighting your best offerings
• Google review trust badge and social proof cards

Take a look — no strings attached and no fee for the preview. If you like the direction and want to put it live on your own domain, I can have it fully set up for you in 48 hours.

Best regards,

Antony Brown
Cali Media Ltd
Direct: 07476 845 289
Web: https://cali-media.ltd"""

        dm_body = f"""Hey {business_name}! 👋 Love your work in {city}. 

Noticed your current site is missing a few modern mobile touchpoints, so I built a free live redesign mockup for you:

👉 {preview_link}

Has instant phone calling, fast quote capture, and clean review proof. Let me know what you think! Cheers, Antony @ Cali Media"""

        return {
            "email_subject": email_subject,
            "email_body": email_body,
            "dm_body": dm_body,
            "preview_link": preview_link
        }

    def generate_page(
        self,
        title: str,
        headline: str,
        subhead: str,
        theme: str,
        cta_text: str,
        features: List[Dict],
        domain: str = "call-on.dad",
        business_name: str = "",
        phone: str = "",
        city: str = "",
        testimonial: Optional[Dict] = None,
        archetype: str = "high-trust-trades"
    ) -> Dict:
        """Generates production semantic HTML5 and styled CSS tailored to the selected 2026 Design Vault Archetype."""
        b_name = business_name or title
        b_phone = phone or "020 8123 4567"
        b_city = city or "United Kingdom"

        accent_map = {
            "trust-blue": {"primary": "#38bdf8", "glow": "rgba(56, 189, 248, 0.25)", "bg": "#090d16", "card": "#101726", "accent": "#0284c7"},
            "warm-amber": {"primary": "#f59e0b", "glow": "rgba(245, 158, 11, 0.25)", "bg": "#0c0e12", "card": "#181410", "accent": "#d97706"},
            "emerald": {"primary": "#10b981", "glow": "rgba(16, 185, 129, 0.25)", "bg": "#08120d", "card": "#0f2018", "accent": "#059669"},
            "crimson": {"primary": "#ef4444", "glow": "rgba(239, 68, 68, 0.25)", "bg": "#120809", "card": "#200e10", "accent": "#dc2626"},
            "luxury-gold": {"primary": "#eab308", "glow": "rgba(234, 179, 8, 0.25)", "bg": "#100e08", "card": "#1a160c", "accent": "#ca8a04"},
            "electric-cyan": {"primary": "#06b6d4", "glow": "rgba(6, 182, 212, 0.25)", "bg": "#081014", "card": "#0d1a20", "accent": "#0891b2"}
        }
        theme_colors = accent_map.get(theme, accent_map["trust-blue"])
        primary = theme_colors["primary"]
        glow = theme_colors["glow"]

        # Validate archetype
        if archetype not in DESIGN_ARCHETYPES:
            archetype = guess_archetype(f"{title} {headline}")

        # 1. BUILD TOP ANNOUNCEMENT BANNER PER ARCHETYPE
        top_banner_html = ""
        if archetype == "high-trust-trades":
            top_banner_html = f"""
  <div class="top-announcement alert-trades">
    <span>🚨 <strong>24/7 Rapid Response:</strong> Engineers on-call in {b_city} · Average Arrival 42 Mins · Zero Callout Fee</span>
    <a href="tel:{b_phone.replace(' ', '')}" class="top-tel">📞 Call Engineer: {b_phone}</a>
  </div>"""
        elif archetype == "bento-modern-saas":
            top_banner_html = f"""
  <div class="top-announcement alert-saas">
    <span><span class="live-dot">●</span> <strong>Platform Status: 99.99% Uptime</strong> · Sovereign UK/EU Cloud Architecture Active</span>
    <span class="top-tel">MCP Bridge v2.4 Online</span>
  </div>"""
        elif archetype == "advocacy-fintech":
            top_banner_html = f"""
  <div class="top-announcement alert-advocacy">
    <span>⚠️ <strong>UK Consumer Warning:</strong> Check the 60-second diagnostic before paying emergency trades callouts</span>
    <a href="#guide-download" class="top-tel">Get £1.99 A4 Checklist &darr;</a>
  </div>"""
        else:
            top_banner_html = f"""
  <div class="top-announcement">
    <span>📍 Serving {b_city} and surrounding areas with 5★ Rated Excellence</span>
    <a href="tel:{b_phone.replace(' ', '')}" class="top-tel">📞 {b_phone}</a>
  </div>"""

        # 2. BUILD ARCHETYPE SPECIFIC CALLOUTS & HERO SUBCOMPONENTS
        hero_badges_html = ""
        if archetype == "bento-modern-saas":
            hero_badges_html = f"""
        <div class="trust-badge saas-badge">
          <span class="badge-icon">✦</span> 2026 Sovereign Architecture · Zero Cold Starts
        </div>"""
        elif archetype == "high-trust-trades":
            hero_badges_html = f"""
        <div class="trust-badge trades-badge">
          <span>★★★★★</span> 4.9 Rating Verified on Checkatrade & Google (210+ Reviews)
        </div>"""
        elif archetype == "advocacy-fintech":
            hero_badges_html = f"""
        <div class="trust-badge advocacy-badge">
          <span>🛡️</span> Call-On Dad & Mom Community Network · Verified Non-Profit Standards
        </div>"""
        else:
            hero_badges_html = f"""
        <div class="trust-badge">
          <span>★★★★★</span> 5.0 Rating on Google & Local Directories
        </div>"""

        # 3. BUILD SERVICES / BENTO GRID
        services_section_html = ""
        if archetype == "bento-modern-saas":
            # Bento Grid Architecture: 2-column & 1-column responsive grid
            bento_cards = ""
            for idx, f in enumerate(features):
                f_title = f.get("title", "Core Service")
                f_desc = f.get("desc", "High quality professional delivery guaranteed.")
                f_price = f.get("price", "SLA Included")
                span_class = "bento-card-wide" if (idx == 0 or idx == 3) else "bento-card-standard"
                bento_cards += f"""
          <div class="bento-card {span_class}">
            <div class="card-glow"></div>
            <div class="bento-header">
              <span class="card-badge">{f_price}</span>
              <span class="telemetry-pill">LIVE METRIC</span>
            </div>
            <div class="service-icon">✦</div>
            <h3 class="service-title">{f_title}</h3>
            <p class="service-desc">{f_desc}</p>
            <div class="bento-footer">
              <a href="#contact" class="service-link">Inspect Architecture &rarr;</a>
            </div>
          </div>"""

            services_section_html = f"""
    <!-- BENTO GRID SHOWCASE (2026 TECH TREND) -->
    <section id="services" class="services-section bento-section">
      <div class="container">
        <div class="section-header">
          <span class="sub-badge">SYSTEM CAPABILITIES</span>
          <h2>Modular 2026 Bento Architecture</h2>
          <p>Engineered for high-throughput resilience, sovereign local control, and real-time execution.</p>
        </div>
        <div class="bento-grid">
{bento_cards}
        </div>
      </div>
    </section>"""
        elif archetype == "advocacy-fintech":
            # Advocacy Cards with £1.99 Toolkit Banner
            cards = ""
            for f in features:
                f_title = f.get("title", "Checklist Item")
                f_desc = f.get("desc", "Clear step-by-step guidance.")
                f_price = f.get("price", "£1.99 Toolkit")
                cards += f"""
          <div class="service-card advocacy-card">
            <div class="card-badge">{f_price}</div>
            <div class="service-icon">📋</div>
            <h3 class="service-title">{f_title}</h3>
            <p class="service-desc">{f_desc}</p>
            <a href="#guide-download" class="service-link">Download Checklist &rarr;</a>
          </div>"""

            services_section_html = f"""
    <!-- ADVOCACY CHECKLIST & £1.99 TOOLKIT SECTION -->
    <section id="services" class="services-section">
      <div class="container">
        <div class="section-header">
          <span class="sub-badge">COMMUNITY CHECKLISTS</span>
          <h2>Self-Help Diagnostics & Fair Pricing</h2>
          <p>Clear, practical toolkits to diagnose issues before calling expensive commercial providers.</p>
        </div>
        <div class="services-grid">
{cards}
        </div>

        <!-- PINNED £1.99 INSTANT A4 DOWNLOAD CARD -->
        <div id="guide-download" class="pinned-guide-banner">
          <div class="guide-banner-left">
            <span class="guide-chip">OFFICIAL A4 PRINT-OFF CHECKLIST • £1.99</span>
            <h3>Instant Emergency Diagnostic Toolkit</h3>
            <p>One-page printable checklist with fair UK price benchmarks, safe isolation steps, and contractor dispute scripts.</p>
          </div>
          <div class="guide-banner-right">
            <a href="#contact" class="btn btn-primary btn-large">Download A4 Guide (£1.99) &rarr;</a>
          </div>
        </div>
      </div>
    </section>"""
        else:
            # Standard & Trades Grid
            cards = ""
            for f in features:
                f_title = f.get("title", "Core Service")
                f_desc = f.get("desc", "High quality professional delivery guaranteed.")
                f_price = f.get("price", "Enquire for Pricing")
                cards += f"""
        <div class="service-card">
          <div class="card-badge">{f_price}</div>
          <div class="service-icon">✦</div>
          <h3 class="service-title">{f_title}</h3>
          <p class="service-desc">{f_desc}</p>
          <a href="#contact" class="service-link">Book This Service &rarr;</a>
        </div>"""

            services_section_html = f"""
    <!-- SERVICES GRID -->
    <section id="services" class="services-section">
      <div class="container">
        <div class="section-header">
          <span class="sub-badge">OUR EXPERTISE</span>
          <h2>Professional Services &amp; Solutions</h2>
          <p>Delivered with precision, transparent pricing, and guaranteed satisfaction in {b_city}.</p>
        </div>
        <div class="services-grid">
{cards}
        </div>
      </div>
    </section>"""

        # 4. MOBILE STICKY DOCK (FOR TRADES & HIGH-CONVERSION)
        mobile_dock_html = ""
        if archetype in ["high-trust-trades", "vitality-health"]:
            mobile_dock_html = f"""
  <!-- THUMB-FRIENDLY FIXED MOBILE ACTION DOCK -->
  <div class="mobile-sticky-dock">
    <a href="tel:{b_phone.replace(' ', '')}" class="dock-btn dock-call">
      <span>📞 Call Now</span>
      <small>{b_phone}</small>
    </a>
    <a href="#contact" class="dock-btn dock-quote">
      <span>⚡ Instant Quote</span>
      <small>15-Min Response</small>
    </a>
  </div>"""

        t_quote = testimonial.get("quote", "Outstanding professionalism from start to finish. Highly recommended!") if testimonial else "Outstanding professionalism from start to finish. Highly recommended!"
        t_author = testimonial.get("author", f"Verified Client · {b_city}") if testimonial else f"Verified Client · {b_city}"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{b_name} — {b_city}</title>
  <link rel="stylesheet" href="style.css">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
</head>
<body class="archetype-{archetype}">
  {top_banner_html}

  <!-- NAVIGATION -->
  <header class="navbar">
    <div class="nav-container">
      <div class="brand">
        <span class="logo-dot"></span>
        <span class="brand-name">{b_name}</span>
      </div>
      <nav class="nav-links">
        <a href="#services">Services</a>
        <a href="#why-us">Why Choose Us</a>
        <a href="#reviews">Reviews</a>
        <a href="tel:{b_phone.replace(' ', '')}" class="nav-phone-btn">📞 {b_phone}</a>
      </nav>
    </div>
  </header>

  <main>
    <!-- HERO SECTION -->
    <section class="hero-section">
      <div class="container hero-content">
        {hero_badges_html}
        <h1 class="hero-title">{headline}</h1>
        <p class="hero-subhead">{subhead}</p>
        <div class="hero-cta-group">
          <a href="#contact" class="btn btn-primary">{cta_text} &rarr;</a>
          <a href="tel:{b_phone.replace(' ', '')}" class="btn btn-secondary">📞 Call {b_phone}</a>
        </div>
        <div class="hero-stats-strip">
          <div class="stat-box"><strong>500+</strong><span>Happy Clients</span></div>
          <div class="stat-box"><strong>45 Mins</strong><span>Rapid Response</span></div>
          <div class="stat-box"><strong>100%</strong><span>Satisfaction Guarantee</span></div>
        </div>
      </div>
    </section>

{services_section_html}

    <!-- TESTIMONIAL & SOCIAL PROOF -->
    <section id="reviews" class="proof-section">
      <div class="container">
        <div class="testimonial-card">
          <div class="stars">★★★★★</div>
          <p class="quote-text">"{t_quote}"</p>
          <div class="author-info">
            <strong>{t_author}</strong>
            <span>Verified 5-Star Local Review</span>
          </div>
        </div>
      </div>
    </section>

    <!-- HIGH-CONVERTING CONTACT / QUOTE CAPTURE FORM -->
    <section id="contact" class="contact-section">
      <div class="container form-container">
        <div class="form-header">
          <h2>Request a Free Consultation or Quote</h2>
          <p>Fill in this quick form and our team in {b_city} will respond within 15 minutes.</p>
        </div>
        <form class="lead-form" onsubmit="event.preventDefault(); alert('Thank you! Your quote request has been received. Our specialist will call you shortly.');">
          <div class="form-row">
            <input type="text" placeholder="Your Name" required class="form-input">
            <input type="tel" placeholder="Phone Number" required class="form-input">
          </div>
          <div class="form-row">
            <input type="email" placeholder="Email Address" required class="form-input">
            <select class="form-input">
              <option value="general">Select Service Needed</option>
              <option value="service-1">Emergency Diagnostics</option>
              <option value="service-2">Full Installation</option>
              <option value="service-3">Maintenance Check</option>
            </select>
          </div>
          <textarea rows="3" placeholder="Briefly describe what you need help with..." class="form-input"></textarea>
          <button type="submit" class="btn btn-primary btn-submit">{cta_text} Now &rarr;</button>
        </form>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-content">
      <div class="footer-brand">
        <strong>{b_name}</strong>
        <p>Serving {b_city} and surrounding areas. Licensed, insured, and certified.</p>
      </div>
      <p class="copyright">&copy; {time.strftime('%Y')} {b_name}. All rights reserved.</p>
      <p class="agency-credit">Designed &amp; Hosted on Sovereign High-Performance Infrastructure by Cali Media Ltd.</p>
    </div>
  </footer>

  {mobile_dock_html}
  <div class="cali-hub-return-dock" style="position:fixed; bottom:16px; left:16px; z-index:999999; display:flex; gap:8px;">
    <button onclick="if(window.parent &amp;&amp; window.parent !== window &amp;&amp; window.parent.closeAppViewer){{window.parent.closeAppViewer();}}else{{window.location.href='/';}}" style="background:#0f172a; color:#14b8a6; border:1px solid #14b8a6; padding:8px 14px; border-radius:20px; font-size:12px; font-weight:700; cursor:pointer; box-shadow:0 4px 14px rgba(0,0,0,0.4); font-family:sans-serif; display:flex; align-items:center; gap:6px;">← Return to Cali Hub</button>
  </div>
</body>
</html>"""

        css_content = f""":root {{
  --bg: {theme_colors['bg']};
  --card: {theme_colors['card']};
  --border: rgba(255, 255, 255, 0.08);
  --border-hover: rgba(255, 255, 255, 0.22);
  --primary: {primary};
  --primary-glow: {glow};
  --primary-accent: {theme_colors['accent']};
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
}}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html {{
  scroll-behavior: smooth;
}}

body {{
  font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
  background-color: var(--bg);
  color: var(--text-main);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  padding-bottom: 60px;
}}

.container {{
  max-width: 1140px;
  margin: 0 auto;
  padding: 0 20px;
}}

.top-announcement {{
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid var(--border);
  padding: 8px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-muted);
}}

.alert-trades {{
  background: rgba(239, 68, 68, 0.12);
  border-bottom: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}}

.alert-saas {{
  background: rgba(6, 182, 212, 0.1);
  border-bottom: 1px solid rgba(6, 182, 212, 0.25);
  color: #a5f3fc;
}}

.alert-advocacy {{
  background: rgba(245, 158, 11, 0.12);
  border-bottom: 1px solid rgba(245, 158, 11, 0.3);
  color: #fde68a;
}}

.live-dot {{
  color: #10b981;
  font-size: 14px;
  margin-right: 4px;
}}

.top-tel {{
  color: var(--primary);
  text-decoration: none;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}}

.navbar {{
  position: sticky;
  top: 0;
  background: rgba(10, 14, 22, 0.88);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
  z-index: 100;
  padding: 14px 0;
}}

.nav-container {{
  max-width: 1140px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}

.brand {{
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 16px;
}}

.logo-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 12px var(--primary);
}}

.brand-name {{
  color: #fff;
  letter-spacing: -0.2px;
}}

.nav-links {{
  display: flex;
  align-items: center;
  gap: 24px;
}}

.nav-links a {{
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: color 0.2s ease;
}}

.nav-links a:hover {{
  color: #fff;
}}

.nav-phone-btn {{
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: var(--primary) !important;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700 !important;
  padding: 6px 14px;
  border-radius: 6px;
}}

.hero-section {{
  padding: 80px 0 60px;
  text-align: center;
  position: relative;
  background: radial-gradient(circle at 50% 0%, var(--primary-glow) 0%, transparent 65%);
}}

.trust-badge {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--primary);
}}

.hero-title {{
  font-size: 44px;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.8px;
  max-width: 820px;
  margin: 0 auto 18px;
  color: #fff;
}}

.hero-subhead {{
  font-size: 16px;
  color: var(--text-muted);
  max-width: 640px;
  margin: 0 auto 34px;
  line-height: 1.6;
}}

.hero-cta-group {{
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-bottom: 48px;
}}

.btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 14px;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}}

.btn-primary {{
  background: var(--primary);
  color: #0f172a;
  box-shadow: 0 4px 20px var(--primary-glow);
}}

.btn-primary:hover {{
  filter: brightness(1.1);
  transform: translateY(-2px);
}}

.btn-secondary {{
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  color: #fff;
}}

.btn-secondary:hover {{
  background: rgba(255, 255, 255, 0.1);
}}

.hero-stats-strip {{
  display: flex;
  justify-content: center;
  gap: 36px;
  border-top: 1px solid var(--border);
  padding-top: 30px;
  max-width: 650px;
  margin: 0 auto;
}}

.stat-box strong {{
  display: block;
  font-size: 20px;
  font-weight: 800;
  color: var(--primary);
}}

.stat-box span {{
  font-size: 11px;
  color: var(--text-muted);
}}

.services-section {{
  padding: 80px 0;
}}

.section-header {{
  text-align: center;
  margin-bottom: 48px;
}}

.sub-badge {{
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1px;
  color: var(--primary);
  text-transform: uppercase;
  display: block;
  margin-bottom: 8px;
}}

.section-header h2 {{
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 12px;
}}

.section-header p {{
  color: var(--text-muted);
  max-width: 580px;
  margin: 0 auto;
  font-size: 14px;
}}

.services-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}}

.service-card {{
  background: var(--card);
  border: 1px solid var(--border);
  padding: 32px;
  border-radius: 14px;
  position: relative;
  transition: transform 0.2s ease, border-color 0.2s ease;
}}

.service-card:hover {{
  transform: translateY(-4px);
  border-color: var(--border-hover);
}}

.card-badge {{
  position: absolute;
  top: 24px;
  right: 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  color: var(--primary);
  font-weight: 700;
}}

.service-icon {{
  color: var(--primary);
  font-size: 22px;
  margin-bottom: 14px;
}}

.service-title {{
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 10px;
}}

.service-desc {{
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 18px;
}}

.service-link {{
  color: var(--primary);
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
}}

/* BENTO GRID (2026 DESIGN VAULT) */
.bento-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}}

.bento-card {{
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 32px;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(12px);
  transition: all 0.25s ease;
}}

.bento-card:hover {{
  border-color: var(--primary);
  transform: translateY(-3px);
}}

.bento-card-wide {{
  grid-column: span 2;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01));
}}

.bento-card-standard {{
  grid-column: span 1;
}}

.bento-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}}

.telemetry-pill {{
  font-size: 9px;
  font-family: 'JetBrains Mono', monospace;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}}

/* PINNED £1.99 ADVOCACY CHECKLIST CARD */
.pinned-guide-banner {{
  margin-top: 40px;
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.12), rgba(15, 23, 42, 0.6));
  border: 2px solid var(--primary);
  border-radius: 16px;
  padding: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}}

.guide-chip {{
  display: inline-block;
  background: var(--primary);
  color: #0f172a;
  font-weight: 800;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  margin-bottom: 10px;
}}

.pinned-guide-banner h3 {{
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 6px;
}}

.pinned-guide-banner p {{
  color: var(--text-muted);
  font-size: 13px;
  max-width: 600px;
}}

/* MOBILE STICKY DOCK */
.mobile-sticky-dock {{
  display: none;
}}

@media (max-width: 768px) {{
  .mobile-sticky-dock {{
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(12px);
    border-top: 1px solid var(--border);
    padding: 10px 16px;
    gap: 12px;
    z-index: 999;
  }}

  .dock-btn {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px 12px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 700;
    font-size: 12px;
  }}

  .dock-call {{
    background: #10b981;
    color: #0f172a;
  }}

  .dock-quote {{
    background: var(--primary);
    color: #0f172a;
  }}

  .dock-btn small {{
    font-size: 10px;
    opacity: 0.85;
  }}

  .bento-grid {{
    grid-template-columns: 1fr;
  }}
  .bento-card-wide {{
    grid-column: span 1;
  }}
  .pinned-guide-banner {{
    flex-direction: column;
    text-align: center;
  }}
  .form-row {{
    flex-direction: column;
  }}
  .nav-links {{
    display: none;
  }}
}}

.proof-section {{
  padding: 40px 0 80px;
}}

.testimonial-card {{
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
  border: 1px solid var(--border);
  padding: 40px;
  border-radius: 16px;
  text-align: center;
  max-width: 780px;
  margin: 0 auto;
}}

.stars {{
  color: #fbbf24;
  font-size: 20px;
  margin-bottom: 14px;
  letter-spacing: 2px;
}}

.quote-text {{
  font-size: 18px;
  font-style: italic;
  margin-bottom: 20px;
  line-height: 1.6;
}}

.author-info strong {{
  display: block;
  font-size: 14px;
}}

.author-info span {{
  font-size: 12px;
  color: var(--text-muted);
}}

.contact-section {{
  padding: 40px 0 100px;
}}

.form-container {{
  max-width: 680px;
  background: var(--card);
  border: 1px solid var(--border);
  padding: 40px;
  border-radius: 16px;
}}

.form-header {{
  text-align: center;
  margin-bottom: 30px;
}}

.form-header h2 {{
  font-size: 26px;
  font-weight: 800;
  margin-bottom: 8px;
}}

.form-header p {{
  color: var(--text-muted);
  font-size: 13px;
}}

.lead-form {{
  display: flex;
  flex-direction: column;
  gap: 16px;
}}

.form-row {{
  display: flex;
  gap: 14px;
}}

.form-input {{
  flex: 1;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border);
  padding: 12px 16px;
  border-radius: 8px;
  color: #fff;
  font-family: inherit;
  font-size: 13px;
  outline: none;
}}

.form-input:focus {{
  border-color: var(--primary);
}}

.btn-submit {{
  width: 100%;
  padding: 14px;
  font-size: 15px;
}}

.site-footer {{
  background: rgba(0, 0, 0, 0.6);
  border-top: 1px solid var(--border);
  padding: 40px 0;
  text-align: center;
}}

.footer-content {{
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  color: var(--text-muted);
  font-size: 12px;
}}

.footer-brand strong {{
  font-size: 15px;
  color: #fff;
  display: block;
  margin-bottom: 4px;
}}

.agency-credit {{
  margin-top: 14px;
  font-size: 11px;
  color: var(--primary);
  opacity: 0.8;
}}
"""

        site_id = f"mockup_{int(time.time())}"
        site_path = self.export_dir / site_id
        site_path.mkdir(parents=True, exist_ok=True)

        (site_path / "index.html").write_text(html_content, encoding="utf-8")
        (site_path / "style.css").write_text(css_content, encoding="utf-8")

        slug = re.sub(r'[^a-zA-Z0-9]', '', b_name.lower())[:18] or site_id
        pitch = self.generate_pitch(business_name=b_name, niche=title, city=b_city, site_url=f"https://{domain}/preview/{site_id}", phone=b_phone)

        metadata = {
            "id": site_id,
            "title": title,
            "business_name": b_name,
            "phone": b_phone,
            "city": b_city,
            "domain": domain,
            "theme": theme,
            "archetype": archetype,
            "headline": headline,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "path": str(site_path).replace("\\", "/"),
            "pitch": pitch,
            "caddyfile_snippet": f"{slug}.call-on.media {{\n    root * /var/www/call-on/sites-generated/{site_id}\n    file_server\n    encode gzip zstd\n    tls {{\n        dns cloudflare {{env.CF_API_TOKEN}}\n    }}\n}}"
        }
        (site_path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        return {
            "ok": True,
            "site_id": site_id,
            "metadata": metadata,
            "pitch": pitch,
            "html": html_content,
            "css": css_content
        }

    def list_generated_sites(self) -> List[Dict]:
        sites = []
        if self.export_dir.exists():
            for d in self.export_dir.iterdir():
                if d.is_dir() and (d / "metadata.json").exists():
                    try:
                        meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
                        sites.append(meta)
                    except Exception:
                        pass
        return sorted(sites, key=lambda x: x.get("created_at", ""), reverse=True)
