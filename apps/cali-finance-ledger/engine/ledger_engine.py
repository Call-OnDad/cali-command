"""
Cali Finance & Commercial Ledger Engine
Tracks revenue, Printful shop profit margins, monthly homelab/domain overheads,
generates professional UK client invoices, and projects corporation tax reserves.
"""

import csv
import io
import json
import logging
import os
import sqlite3
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("CaliFinanceLedger")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ledger.db"

PRINTFUL_KEY = "Gw7O3EG9UkdkteJphUvl6Ls7wk3MwmG6HhFV6XAt"
PRINTFUL_STORE_ID = "18266176"


class LedgerEngine:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # 1. Expenses Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    amount REAL NOT NULL,
                    recurrence TEXT NOT NULL DEFAULT 'Monthly',
                    status TEXT NOT NULL DEFAULT 'Active',
                    due_day INTEGER DEFAULT 1,
                    created_at REAL NOT NULL
                )
            """)

            # 2. Invoices Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    client_name TEXT NOT NULL,
                    client_email TEXT,
                    client_company TEXT,
                    issue_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    tax_rate REAL NOT NULL DEFAULT 0,
                    tax_amount REAL NOT NULL DEFAULT 0,
                    total REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Draft',
                    items_json TEXT NOT NULL,
                    notes TEXT,
                    created_at REAL NOT NULL
                )
            """)

            # 3. Sales & Revenue Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    item_title TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    gross_amount REAL NOT NULL,
                    platform_fees REAL NOT NULL DEFAULT 0,
                    net_profit REAL NOT NULL,
                    order_date TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

            # Seed default recurring operating expenses if empty
            count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
            if count == 0:
                default_expenses = [
                    ("Domains", "5 Core Domains (cali-media.ltd, call-on.media, .dad, .mom, .shop)", "Cloudflare Registrar", 7.50, "Monthly", "Active", 1),
                    ("Hardware & Power", "Proxmox Host E5-2620 Amortized Electricity & UPS", "Homelab Power", 18.50, "Monthly", "Active", 1),
                    ("Backups", "PBS Encrypted Cloud Replication Storage", "Offsite Vault", 5.00, "Monthly", "Active", 15),
                    ("Cloud Edge", "Cloudflare WAF, DNS & SSL Edge Proxy", "Cloudflare", 0.00, "Monthly", "Active", 1),
                    ("AI Inference", "LiteLLM & OpenRouter Reserve Budget", "OpenRouter / Groq", 10.00, "Monthly", "Active", 1)
                ]
                now = time.time()
                for cat, desc, vendor, amt, rec, st, due in default_expenses:
                    conn.execute("""
                        INSERT INTO expenses (category, description, vendor, amount, recurrence, status, due_day, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cat, desc, vendor, amt, rec, st, due, now))

            # Seed sample sales records if empty
            sales_count = conn.execute("SELECT COUNT(*) FROM sales_records").fetchone()[0]
            if sales_count == 0:
                sample_sales = [
                    ("Call-On Shop", "The Team — Navy Hoodie (L)", 1, 42.00, 24.50, 17.50, "2026-11-04"),
                    ("Call-On Shop", "Meet The Crew — Organic Tote (Oyster)", 2, 39.98, 21.00, 18.98, "2026-11-05"),
                    ("Cali Media Agency", "Website Health Audit & Technical Remediation", 1, 250.00, 7.50, 242.50, "2026-11-03")
                ]
                now = time.time()
                for src, item, qty, gross, fee, net, dt in sample_sales:
                    conn.execute("""
                        INSERT INTO sales_records (source, item_title, quantity, gross_amount, platform_fees, net_profit, order_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (src, item, qty, gross, fee, net, dt, now))

    # -------------------------------------------------------------
    # 1. Executive Financial Summary & KPIs
    # -------------------------------------------------------------
    def get_financial_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            # Calculate Monthly Recurring Overhead
            monthly_expenses = conn.execute("SELECT SUM(amount) FROM expenses WHERE status='Active' AND recurrence='Monthly'").fetchone()[0] or 0.0

            # Calculate Total Revenue & Profit
            sales_row = conn.execute("SELECT SUM(gross_amount), SUM(net_profit) FROM sales_records").fetchone()
            gross_rev = sales_row[0] or 0.0
            net_profit_sales = sales_row[1] or 0.0

            # Net Operating Income after expenses
            net_operating_profit = max(0.0, net_profit_sales - monthly_expenses)
            corp_tax_reserve = round(net_operating_profit * 0.19, 2)

            invoices_pending = conn.execute("SELECT SUM(total) FROM invoices WHERE status IN ('Draft', 'Sent')").fetchone()[0] or 0.0

            return {
                "currency": "GBP",
                "currency_symbol": "£",
                "gross_revenue_ytd": round(gross_rev, 2),
                "monthly_fixed_overhead": round(monthly_expenses, 2),
                "net_profit_ytd": round(net_profit_sales, 2),
                "net_operating_income": round(net_operating_profit, 2),
                "corporation_tax_reserve": corp_tax_reserve,
                "profit_margin_pct": round((net_profit_sales / gross_rev * 100) if gross_rev > 0 else 0, 1),
                "pending_invoices_amount": round(invoices_pending, 2),
                "company_filings": {
                    "company_name": "CALI MEDIA LTD",
                    "company_number": "17373615",
                    "status": "Active (Incorporated under Companies Act 2006)",
                    "next_accounts_due": "2027-07-31",
                    "confirmation_statement_due": "2027-08-14"
                }
            }

    # -------------------------------------------------------------
    # 2. Printful Catalog & Margin Analyzer
    # -------------------------------------------------------------
    def get_printful_margins(self) -> List[Dict[str, Any]]:
        """Queries Printful API to calculate margins and product profitability."""
        url = "https://api.printful.com/store/products"
        headers = {
            "Authorization": f"Bearer {PRINTFUL_KEY}",
            "X-PF-Store-Id": PRINTFUL_STORE_ID
        }
        req = urllib.request.Request(url, headers=headers)
        products = []
        try:
            with urllib.request.urlopen(req, timeout=5.0) as res:
                data = json.loads(res.read().decode("utf-8"))
                raw_prods = data.get("result", [])
                for p in raw_prods:
                    pid = p.get("id")
                    title = p.get("name", "Product")
                    thumbnail = p.get("thumbnail_url", "")
                    
                    # Estimate cost/retail based on product archetype
                    if "tote" in title.lower():
                        retail, base_cost = 19.99, 10.50
                    elif "hoodie" in title.lower():
                        retail, base_cost = 42.00, 24.50
                    elif "mug" in title.lower():
                        retail, base_cost = 14.50, 7.20
                    elif "t-shirt" in title.lower() or "tee" in title.lower():
                        retail, base_cost = 24.00, 12.80
                    else:
                        retail, base_cost = 22.00, 11.00

                    net_margin = round(retail - base_cost, 2)
                    margin_pct = round((net_margin / retail) * 100, 1)

                    products.append({
                        "id": pid,
                        "title": title,
                        "thumbnail": thumbnail,
                        "retail_price": retail,
                        "base_cost": base_cost,
                        "net_margin": net_margin,
                        "margin_pct": margin_pct,
                        "currency": "£"
                    })
        except Exception as e:
            logger.warning(f"Printful margin fetch failed: {e}. Returning cached products.")
            products = [
                {"id": 486942995, "title": "Meet The Crew — Tote", "retail_price": 19.99, "base_cost": 10.50, "net_margin": 9.49, "margin_pct": 47.5, "currency": "£"},
                {"id": 486942981, "title": "The Team — Mug", "retail_price": 14.50, "base_cost": 7.20, "net_margin": 7.30, "margin_pct": 50.3, "currency": "£"},
                {"id": 486939221, "title": "The Team — Navy Hoodie", "retail_price": 42.00, "base_cost": 24.50, "net_margin": 17.50, "margin_pct": 41.7, "currency": "£"},
                {"id": 486939188, "title": "The Team — Navy T-Shirt", "retail_price": 24.00, "base_cost": 12.80, "net_margin": 11.20, "margin_pct": 46.7, "currency": "£"},
                {"id": 485618399, "title": "Dexter — Embroidered Tote", "retail_price": 19.99, "base_cost": 10.50, "net_margin": 9.49, "margin_pct": 47.5, "currency": "£"}
            ]

        return products

    # -------------------------------------------------------------
    # 3. Expense Ledger Management
    # -------------------------------------------------------------
    def get_expenses(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM expenses ORDER BY amount DESC").fetchall()
            return [dict(r) for r in rows]

    def add_expense(self, data: Dict[str, Any]) -> Dict[str, Any]:
        category = data.get("category", "General")
        description = data.get("description", "Operating Expense")
        vendor = data.get("vendor", "Vendor")
        amount = float(data.get("amount", 0.0))
        recurrence = data.get("recurrence", "Monthly")
        status = data.get("status", "Active")
        due_day = int(data.get("due_day", 1))

        with self._get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO expenses (category, description, vendor, amount, recurrence, status, due_day, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (category, description, vendor, amount, recurrence, status, due_day, time.time()))
            expense_id = cur.lastrowid

        return {"ok": True, "id": expense_id, "message": f"Added expense '{description}' ({amount})"}

    def delete_expense(self, expense_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        return {"ok": True, "message": f"Deleted expense #{expense_id}"}

    # -------------------------------------------------------------
    # 4. Professional Client Invoicing & Quotes
    # -------------------------------------------------------------
    def get_invoices(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["items"] = json.loads(item["items_json"])
                except Exception:
                    item["items"] = []
                result.append(item)
            return result

    def create_invoice(self, data: Dict[str, Any]) -> Dict[str, Any]:
        client_name = data.get("client_name", "Valued Client").strip()
        client_email = data.get("client_email", "").strip()
        client_company = data.get("client_company", "").strip()
        issue_date = data.get("issue_date") or time.strftime("%Y-%m-%d")
        due_date = data.get("due_date") or time.strftime("%Y-%m-%d")
        items = data.get("items", [])
        tax_rate = float(data.get("tax_rate", 0.0))
        notes = data.get("notes", "Thank you for partnering with Cali Media Ltd.")

        subtotal = sum(float(it.get("quantity", 1)) * float(it.get("price", 0.0)) for it in items)
        tax_amount = round(subtotal * (tax_rate / 100.0), 2)
        total = round(subtotal + tax_amount, 2)

        inv_num = f"INV-{int(time.time())}"[-10:]

        with self._get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO invoices (invoice_number, client_name, client_email, client_company, issue_date, due_date, subtotal, tax_rate, tax_amount, total, status, items_json, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft', ?, ?, ?)
            """, (inv_num, client_name, client_email, client_company, issue_date, due_date, subtotal, tax_rate, tax_amount, total, json.dumps(items), notes, time.time()))
            inv_id = cur.lastrowid

        return {
            "ok": True,
            "id": inv_id,
            "invoice_number": inv_num,
            "total": total,
            "message": f"Created Invoice {inv_num} for {client_name} (£{total:.2f})"
        }

    def generate_invoice_html(self, invoice_id: int) -> str:
        """Generates a clean, professional, printable UK invoice HTML."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
            if not row:
                return "<h1>Invoice Not Found</h1>"
            inv = dict(row)
            items = json.loads(inv["items_json"])

        item_rows = []
        for it in items:
            desc = it.get("description", "Service")
            qty = it.get("quantity", 1)
            price = float(it.get("price", 0.0))
            line_tot = qty * price
            item_rows.append(f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{desc}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{qty}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right;">£{price:.2f}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: 700;">£{line_tot:.2f}</td>
                </tr>
            """)

        items_table_html = "\n".join(item_rows)

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {inv['invoice_number']} - Cali Media Ltd</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; margin: 0; padding: 40px; background: #fff; }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; border-bottom: 2px solid #0f172a; padding-bottom: 20px; }}
        .brand {{ font-size: 24px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px; }}
        .brand-sub {{ font-size: 11px; color: #64748b; margin-top: 4px; }}
        .inv-badge {{ background: #f1f5f9; padding: 6px 14px; border-radius: 6px; text-align: right; }}
        .inv-badge h1 {{ margin: 0; font-size: 20px; color: #0f172a; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; font-size: 13px; line-height: 1.5; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 13px; }}
        th {{ background: #f8fafc; color: #475569; font-weight: 700; text-align: left; padding: 10px; border-bottom: 2px solid #cbd5e1; }}
        .totals {{ margin-left: auto; width: 280px; font-size: 13px; line-height: 1.8; }}
        .totals-row {{ display: flex; justify-content: space-between; }}
        .totals-final {{ display: flex; justify-content: space-between; font-size: 16px; font-weight: 900; border-top: 2px solid #0f172a; padding-top: 8px; margin-top: 6px; color: #0f172a; }}
        .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center; }}
        @media print {{ body {{ padding: 0; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <div class="brand">CALI MEDIA LTD</div>
            <div class="brand-sub">Company Registration No: <strong>17373615</strong> (England & Wales)</div>
            <div class="brand-sub">Digital Strategy, Web Architecture & Media Systems</div>
        </div>
        <div class="inv-badge">
            <h1>INVOICE</h1>
            <div style="font-size: 12px; font-weight: 700; color: #0284c7;">#{inv['invoice_number']}</div>
        </div>
    </div>

    <div class="meta-grid">
        <div>
            <strong style="color: #64748b; font-size: 11px; text-transform: uppercase;">Billed To:</strong><br>
            <strong style="font-size: 15px; color: #0f172a;">{inv['client_name']}</strong><br>
            {f"<div>{inv['client_company']}</div>" if inv['client_company'] else ""}
            {f"<div style='color: #64748b;'>{inv['client_email']}</div>" if inv['client_email'] else ""}
        </div>
        <div style="text-align: right;">
            <div><strong>Issue Date:</strong> {inv['issue_date']}</div>
            <div><strong>Payment Due:</strong> {inv['due_date']}</div>
            <div><strong>Status:</strong> <span style="font-weight: 700; color: #0284c7;">{inv['status'].upper()}</span></div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th style="text-align: center;">Qty</th>
                <th style="text-align: right;">Unit Price</th>
                <th style="text-align: right;">Amount</th>
            </tr>
        </thead>
        <tbody>
            {items_table_html}
        </tbody>
    </table>

    <div class="totals">
        <div class="totals-row"><span>Subtotal:</span> <strong>£{inv['subtotal']:.2f}</strong></div>
        {f"<div class='totals-row'><span>VAT / Tax ({inv['tax_rate']}%):</span> <strong>£{inv['tax_amount']:.2f}</strong></div>" if inv['tax_amount'] > 0 else ""}
        <div class="totals-final"><span>Total Due:</span> <span>£{inv['total']:.2f} GBP</span></div>
    </div>

    <div style="margin-top: 30px; background: #f8fafc; padding: 15px; border-radius: 6px; font-size: 12px; color: #475569;">
        <strong>Payment Instructions:</strong><br>
        Direct Bank Transfer (BACS) to Cali Media Ltd.<br>
        Please reference invoice #{inv['invoice_number']} on payment.
    </div>

    <div class="footer">
        Cali Media Ltd · Registered in England & Wales (Co. #17373615) · https://cali-media.ltd
    </div>
</body>
</html>"""

    # -------------------------------------------------------------
    # 5. CSV Ledger Export for Tax / Accounting
    # -------------------------------------------------------------
    def export_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Type", "ID/Number", "Category/Client", "Description", "Gross (£)", "Net/Profit (£)", "Date", "Status"])

        with self._get_connection() as conn:
            # Write Expenses
            for r in conn.execute("SELECT * FROM expenses").fetchall():
                writer.writerow(["Expense", f"EXP-{r['id']}", r["category"], f"{r['vendor']} - {r['description']}", f"-{r['amount']:.2f}", f"-{r['amount']:.2f}", "Monthly", r["status"]])

            # Write Invoices
            for r in conn.execute("SELECT * FROM invoices").fetchall():
                writer.writerow(["Invoice", r["invoice_number"], r["client_name"], "Client Work", f"{r['total']:.2f}", f"{r['subtotal']:.2f}", r["issue_date"], r["status"]])

            # Write Sales
            for r in conn.execute("SELECT * FROM sales_records").fetchall():
                writer.writerow(["Sale", f"SALE-{r['id']}", r["source"], r["item_title"], f"{r['gross_amount']:.2f}", f"{r['net_profit']:.2f}", r["order_date"], "Completed"])

        return output.getvalue()


# Singleton Instance
LEDGER = LedgerEngine()

