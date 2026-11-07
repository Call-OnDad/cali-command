# Cali Command 🌟🛡️

> **Sovereign Autonomous Operating System & Modular Department Suites for Businesses & Creators.**  
> A decoupled fleet of native applications running locally without subscription locks, cloud fees, or single-point-of-failure architectures.

---

## 🏛️ What is Cali Command?

Cali Command is an autonomous operational headquarters. Instead of one brittle monolithic system where a bug in one service crashes the entire company, Cali Command is built from **independent, modular department suites**.

Every department runs on its own local port with its own lightweight Python server, native UI, and background engine. You can run the **entire fleet simultaneously**, or run **just one module** completely offline as a zero-dependency fallback.

---

## 🧭 Fleet Port Directory

| Department Suite | Port | Description | Standalone Launcher |
| :--- | :--- | :--- | :--- |
| **👑 Mission Control Central Hub** | `8800` | Master executive dashboard, fleet status, and cross-suite orchestrator | `apps/cali-central-hub/Launch-Central-Hub.cmd` |
| **🎬 Video & Media Studio** | `8790` | Syllable-accurate neural lip-sync, Piper TTS, presentation cards, multi-track NLE | `apps/cali-video-studio/Launch-Studio.cmd` |
| **🌐 Website Creator Studio** | `8789` | Autonomous website builder, theme generator, and component designer | `apps/cali-website-creator/Launch-Website-Creator.cmd` |
| **📱 Social Media & Publishing Hub** | `8793` | Multi-network social scheduler, publisher (Echo), 1-click video distributor | `apps/cali-social-hub/Launch-Social-Hub.cmd` |
| **🔍 SEO & Search Radar** | `8791` | Multi-domain rank tracking, crawler, Schema.org optimizer | `apps/cali-seo-radar/Launch-SEO-Radar.cmd` |
| **💻 Dev & Code Release Workbench** | `8792` | Automated testing, git workspace monitor, and release packager | `apps/cali-dev-workbench/Launch-Dev-Workbench.cmd` |
| **⚙️ Daily Briefing & Automations** | `8794` | Scheduled tasks, daemons, morning briefs, and automated reports | `apps/cali-automations-runner/Launch-Automations-Runner.cmd` |
| **👥 Community Sites & Shop Suite** | `8795` | Self-hosted community forums, member directories, and shop sync | `apps/cali-community-sites/Launch-Community-Sites.cmd` |
| **🩺 Website Health & Homelab Radar** | `8796` | Ping radar, uptime checks, SSL monitoring, homelab server health | `apps/cali-health-checker/Launch-Health-Checker.cmd` |
| **🛡️ Security & Threat Radar** | `8797` | Egress firewalls, token leak detection, and local intrusion monitoring | `apps/cali-security-radar/Launch-Security-Radar.cmd` |
| **📄 Docs, Reports & Knowledge Centre** | `8798` | Automated PDF report generator, Markdown documentation vault | `apps/cali-docs-reports/Launch-Docs-Reports.cmd` |
| **💳 Commercial & Finance Ledger** | `8799` | Local expense tracking, invoice generation, subscription auditor | `apps/cali-finance-ledger/Launch-Finance-Ledger.cmd` |

---

## 🚀 Quickstart

### 1. Boot the Entire Fleet
Double-click [`Launch-All-Cali-Fleet.cmd`](Launch-All-Cali-Fleet.cmd) (or run `./Launch-All-Cali-Fleet.ps1` in PowerShell).

This starts all 12 department engines in the background and automatically opens **Mission Control at `http://127.0.0.1:8800`**.

### 2. Run a Single Department (Fallback Mode)
If your main homelab or server equipment is ever offline, or if you only need one capability on a laptop:
1. Navigate into that department's folder (e.g. `cd apps/cali-website-creator/`).
2. Double-click its launcher (e.g. `Launch-Website-Creator.cmd`).
3. Open its dedicated port in your browser.

---

## 🔒 Privacy & Clean Open Source

* **100% Sanitized:** No private family voice identities, server tokens, proprietary passwords, or client databases are committed.
* **Environment Templates:** Copy `.env.example` to `.env` in any suite to add your own API credentials.
* **Open Source:** Released under the permissive [MIT Licence](LICENSE).
