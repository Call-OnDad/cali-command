"""
doc_vault.py - Document repository indexing, Companies House filings, historical lessons learned, and OnlyOffice workspace bridge.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger("cali.docs.vault")

class DocVault:
    def __init__(self, config: Dict):
        self.config = config
        self.workspace_root = Path(self.config.get("workspace_root", "d:/The Cali Project"))
        self.docs_dir = self.workspace_root / "docs"

    def list_documents(self) -> List[Dict]:
        items = []

        # 1. Historical & Sovereign System Architecture & Lessons Learned
        core_records = [
            {
                "id": "lessons-learned-history",
                "title": "Cali Lessons Learned & Operational Post-Mortems Archive",
                "category": "Knowledge Base & Lessons Learned",
                "type": "Engineering Retrospective",
                "last_modified": "2026-11-04",
                "path": "docs/audits/2026-10-17-two-auditors-and-shared-lessons.md",
                "summary": "Durable capture of engineering lessons, ChromaDB ingest pipeline, deduplication at 0.92 threshold, and hallucination prevention."
            },
            {
                "id": "standalone-auditor-guide",
                "title": "Standalone Cali Auditor Architecture & Helm Retirement",
                "category": "Code Quality & Governance",
                "type": "Audit Specification",
                "last_modified": "2026-10-24",
                "path": "docs/audits/2026-10-24-standalone-auditor-and-helm-retirement.md",
                "summary": "Restoration of original chunk-hash source scanner, read-only boundary checks, and safe human-in-the-loop review."
            },
            {
                "id": "agent-caps-audit-trail",
                "title": "Unified Agent Audit Trail & Capability Bounds",
                "category": "AI Safety & Compliance",
                "type": "Safety Runbook",
                "last_modified": "2026-10-18",
                "path": "docs/audits/2026-10-18-agent-caps-and-audit-trail.md",
                "summary": "Every agent tool call audit trail with credential redaction, trace correlation, and hard capability limits."
            },
            {
                "id": "sovereign-atlas",
                "title": "Cali Sovereign System Architecture & Fleet Topology",
                "category": "Infrastructure Architecture",
                "type": "System Blueprint",
                "last_modified": "2026-11-05",
                "path": "docs/showcase/system-map/CALI-SYSTEM-MAP.md",
                "summary": "Single-host Proxmox topology, 31 sovereign containers, zero external dependencies, isolated secure bridge networking."
            },
            {
                "id": "overwatch-resolution",
                "title": "Overwatch Defect Audit & Resolution Log",
                "category": "Technical Compliance",
                "type": "Audit Report",
                "last_modified": "2026-11-04",
                "path": "docs/audits/2026-11-04-overwatch-review.md",
                "summary": "Systematic review of website findings, defect resolution queues, and live verification."
            },
            {
                "id": "modules-benchmark",
                "title": "Cali 10-Department Modular Architecture Research",
                "category": "Architecture Strategy",
                "type": "System Research",
                "last_modified": "2026-11-06",
                "path": "docs/MODULES_BENCHMARK_RESEARCH.md",
                "summary": "Zero-cost sovereign department architecture with dedicated local microservices on ports 8790-8800."
            }
        ]
        items.extend(core_records)

        # 2. Curated standard corporate archives
        standard_docs = [
            {"id": "corp-articles", "title": "Cali Media Ltd Articles of Association", "category": "Corporate Governance", "type": "Legal Policy", "last_modified": "2026-10-14", "path": "docs/corporate/articles.pdf", "summary": "Official Articles of Association for CALI MEDIA LTD (Co. #17373615)."},
            {"id": "dad-guidelines", "title": "Call-On Dad Volunteer Mentor Guidelines", "category": "Community Policies", "type": "Operations SOP", "last_modified": "2026-10-22", "path": "docs/community/dad-mentor-sop.md", "summary": "Safeguarding, peer mentorship standards, and privacy protocols for Call-On Dad."},
            {"id": "mom-handbook", "title": "Call-On Mom Peer Circles Handbook", "category": "Community Policies", "type": "Operations SOP", "last_modified": "2026-10-24", "path": "docs/community/mom-circles-sop.md", "summary": "Support network guidelines and budgeting circles documentation for Call-On Mom."},
            {"id": "printful-agree", "title": "Printful E-Commerce Merchandising Agreement", "category": "Commercial Contracts", "type": "Vendor Contract", "last_modified": "2026-10-29", "path": "docs/commercial/printful-sync.md", "summary": "On-demand manufacturing and API fulfillment specifications for Call-On Shop."},
            {"id": "dr-plan", "title": "Cloudflare & Proxmox Disaster Recovery Plan", "category": "Infrastructure SOP", "type": "Disaster Recovery", "last_modified": "2026-11-02", "path": "docs/infra/disaster-recovery.md", "summary": "Proxmox Backup Server (PBS) nightly verification, cold snapshot recovery, and failover runbooks."}
        ]
        items.extend(standard_docs)

        # 3. Dynamic scan of docs/audits directory
        audits_dir = self.docs_dir / "audits"
        if audits_dir.exists():
            for f in sorted(audits_dir.glob("*.md"), reverse=True)[:8]:
                clean_name = f.stem.replace("-", " ").title()
                items.append({
                    "id": f.stem,
                    "title": f"Audit Log: {clean_name}",
                    "category": "Historical Audit Trails",
                    "type": "Audit Log",
                    "last_modified": time.strftime("%Y-%m-%d", time.localtime(f.stat().st_mtime)),
                    "path": str(f.relative_to(self.workspace_root)).replace("\\", "/"),
                    "summary": f"Historical system audit and verification record for {clean_name}."
                })

        return items

    def search_knowledge(self, query: str) -> List[Dict]:
        query = query.lower()
        all_docs = self.list_documents()
        matched = []
        for d in all_docs:
            if (query in d.get("title", "").lower() or 
                query in d.get("category", "").lower() or 
                query in d.get("summary", "").lower() or 
                query in d.get("type", "").lower()):
                matched.append(d)
        return matched

    def get_corporate_filings(self) -> Dict:
        return {
            "company_name": "CALI MEDIA LTD",
            "company_number": self.config.get("companies_house", {}).get("company_number", "17373615"),
            "company_status": "Active (Incorporated under Companies Act 2006)",
            "jurisdiction": "England and Wales",
            "accounts_next_due": "2027-07-31",
            "confirmation_statement_next_due": "2027-06-15",
            "onlyoffice_endpoint": self.config.get("onlyoffice", {}).get("url", "https://office.call-on.media"),
            "registered_office": "London, United Kingdom",
            "sic_codes": ["62012 - Business and domestic software development", "58190 - Other publishing activities"]
        }
