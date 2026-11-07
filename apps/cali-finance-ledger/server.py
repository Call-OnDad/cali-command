"""
server.py - Native HTTP Server for Cali Commercial & Finance Ledger
Runs independently on port 8799, providing real-time financial tracking,
Printful e-commerce margins, expense management, and client invoice generation.
"""

import json
import logging
import mimetypes
import os
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from engine.ledger_engine import LEDGER

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cali.finance.server")

PORT = 8799


class FinanceHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "ui"), **kwargs)

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/api/status":
            self.send_json({"status": "ONLINE", "module": "cali-finance-ledger", "port": PORT, "version": "1.0.0"})
            return

        if path == "/api/finance/summary":
            self.send_json(LEDGER.get_financial_summary())
            return

        if path == "/api/finance/margins":
            self.send_json({"products": LEDGER.get_printful_margins()})
            return

        if path == "/api/finance/expenses":
            self.send_json({"expenses": LEDGER.get_expenses()})
            return

        if path == "/api/finance/invoices":
            self.send_json({"invoices": LEDGER.get_invoices()})
            return

        if path.startswith("/api/finance/invoices/") and path.endswith("/html"):
            parts = path.strip("/").split("/")
            try:
                inv_id = int(parts[3])
                html = LEDGER.generate_invoice_html(inv_id)
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                self.send_json({"error": str(e)}, status=400)
                return

        if path == "/api/finance/export/csv":
            csv_data = LEDGER.export_csv().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=\"cali_media_ledger.csv\"")
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)
            return

        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        data = json.loads(post_body) if post_body else {}

        if path == "/api/finance/expenses":
            res = LEDGER.add_expense(data)
            self.send_json(res)
            return

        if path == "/api/finance/expenses/delete":
            expense_id = int(data.get("id", 0))
            res = LEDGER.delete_expense(expense_id)
            self.send_json(res)
            return

        if path == "/api/finance/invoices":
            res = LEDGER.create_invoice(data)
            self.send_json(res)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)


def run_server():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), FinanceHandler)
    logger.info(f"Cali Commercial & Finance Ledger running on http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Finance Ledger server stopped.")


if __name__ == "__main__":
    run_server()
