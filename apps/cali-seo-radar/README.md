# Cali SEO & Search Radar Suite (`apps/cali-seo-radar`)

Standalone, decoupled SEO and search intelligence suite for Cali Media Group. Runs completely natively on local hardware without depending on or locking the Cali Chat Server.

## Features

1. **Multi-Domain Fleet Radar:**
   - Active tracking across all 5 core brand domains:
     - `cali-media.ltd` (Corporate & Autonomous Platform)
     - `call-on.media` (Video & Creative Agency)
     - `call-on.dad` (Consumer Guides & Handyman Advice)
     - `call-on.mom` (Household Budgeting & Home Care)
     - `call-on.shop` (E-Commerce & Mascot Merchandise)
   - Dynamic registration for adding new domains, landing pages, and microsites on the fly.

2. **Autonomous SERP Tracking & CT120 SerpBear Client:**
   - Integrates with SerpBear running in Proxmox container **CT120**.
   - Autonomous Fallback: If CT120 is offline or sleeping, the radar maintains local ranking histories, 7-day sparkline shift trends, keyword difficulty, and search volumes.
   - Position shift indicators: ▲ gains, ▼ drops, stable rankings.

3. **High-Speed On-Page Site Crawler:**
   - Native HTTP inspection with zero external dependencies.
   - Extracts page titles, meta descriptions, canonical URLs, robots directives, OpenGraph tags, and Twitter cards.
   - Audits headings hierarchy (H1-H3), image missing alt attributes, and response latency.
   - Calculates automated SEO Health Score (0-100%).

4. **Real-Time Content Auditor & Schema Generator:**
   - Live on-page article optimizer.
   - Target keyword density calculation with stuffing prevention safeguards (1.0% to 2.5% optimal).
   - Flesch Reading Ease score & sentence length pacing.
   - Google SERP Simulator card (Desktop & Mobile visual preview).
   - Instant Schema.org JSON-LD generator (Article, Organization, Breadcrumb).

## How to Launch

- **Double-click:** `Launch-SEO-Radar.cmd`
- **Or PowerShell:** `.\Launch-SEO-Radar.ps1`
- **Browser URL:** `http://127.0.0.1:8791`
