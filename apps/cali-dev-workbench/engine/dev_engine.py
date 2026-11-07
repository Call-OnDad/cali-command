"""
Cali Dev & Code Release Workbench Engine
Provides Git repository inspection, side-by-side diffs, automated credential leak scanning,
safe code patch review queue, and deployment receipts.
"""

import json
import logging
import os
import re
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("CaliDevWorkbench")

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = Path("D:/The Cali Project")
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "patches.db"

LEAK_PATTERNS = [
    (re.compile(r"sk-or-v1-[a-f0-9]{64}"), "OpenRouter Live API Key"),
    (re.compile(r"gsk_[a-zA-Z0-9]{40,}"), "Groq API Key"),
    (re.compile(r"sk_live_[a-zA-Z0-9]{24,}"), "Stripe Live Secret Key"),
    (re.compile(r"rk_live_[a-zA-Z0-9]{24,}"), "Stripe Live Restricted Key"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"PVEAPIToken=[a-zA-Z0-9@!=-]{30,}"), "Proxmox Live API Token"),
    (re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"), "Private Cryptographic Key")
]


class DevEngine:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            # 1. Patch proposals table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patch_proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_env TEXT NOT NULL DEFAULT 'local',
                    old_text TEXT NOT NULL,
                    new_text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    author TEXT NOT NULL DEFAULT 'Antony / Cali',
                    applied_at REAL,
                    created_at REAL NOT NULL
                )
            """)

            # 2. Deployment receipts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deployment_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    release_tag TEXT NOT NULL,
                    action TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp REAL NOT NULL
                )
            """)

            # Seed sample reviewable patch if empty
            count = conn.execute("SELECT COUNT(*) FROM patch_proposals").fetchone()[0]
            if count == 0:
                conn.execute("""
                    INSERT INTO patch_proposals (file_path, description, target_env, old_text, new_text, status, author, created_at)
                    VALUES (?, ?, ?, ?, ?, 'pending', 'Cali Overwatch', ?)
                """, (
                    "server/cali_llm_config.py",
                    "Update primary model fallback to Groq 70B zero-credit safety tier",
                    "local",
                    "model = 'nexus-main'",
                    "model = 'fb-groq-70b'",
                    time.time()
                ))

    # -------------------------------------------------------------
    # 1. Git Repository Status & Commits
    # -------------------------------------------------------------
    def get_git_status(self) -> Dict[str, Any]:
        """Inspects Git working tree, modified files, untracked files, and recent commit history."""
        # 1. Branch
        branch = "master"
        try:
            r = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=4.0)
            if r.returncode == 0 and r.stdout.strip():
                branch = r.stdout.strip()
        except Exception:
            pass

        # 2. Porcelain Status
        modified = []
        untracked = []
        try:
            r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=4.0)
            if r.returncode == 0:
                for line in r.stdout.splitlines():
                    if not line.strip():
                        continue
                    status_code = line[:2]
                    filename = line[3:].strip()
                    if "??" in status_code:
                        untracked.append(filename)
                    else:
                        modified.append({"file": filename, "status": status_code.strip()})
        except Exception as e:
            logger.warning(f"Git status failed: {e}")

        # 3. Recent Commits
        commits = []
        try:
            r = subprocess.run(["git", "log", "-n", "10", "--pretty=format:%h|%an|%ar|%s"], capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=4.0)
            if r.returncode == 0:
                for line in r.stdout.splitlines():
                    if "|" in line:
                        parts = line.split("|", 3)
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "relative_time": parts[2],
                            "subject": parts[3]
                        })
        except Exception:
            pass

        return {
            "branch": branch,
            "is_clean": len(modified) == 0,
            "modified_count": len(modified),
            "untracked_count": len(untracked),
            "modified_files": modified,
            "untracked_files": untracked[:15],
            "recent_commits": commits
        }

    # -------------------------------------------------------------
    # 2. Unified Diff Viewer
    # -------------------------------------------------------------
    def get_file_diff(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Generates unified diff for a single modified file or the entire working tree."""
        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=6.0)
            diff_text = r.stdout
            if not diff_text and file_path:
                # Check untracked file preview
                full_p = REPO_ROOT / file_path
                if full_p.exists() and full_p.is_file():
                    content = full_p.read_text(encoding="utf-8", errors="ignore")[:2000]
                    diff_text = f"--- /dev/null\n+++ b/{file_path}\n@@ -0,0 +1,50 @@\n" + "\n".join("+" + l for l in content.splitlines())
            return {"file": file_path or "working_tree", "diff": diff_text or "(No uncommitted diff)"}
        except Exception as e:
            return {"file": file_path or "working_tree", "diff": f"Error loading diff: {e}"}

    # -------------------------------------------------------------
    # 3. Secret & Credential Leak Scanner
    # -------------------------------------------------------------
    def scan_for_secrets(self) -> Dict[str, Any]:
        """Scans modified files and tracked source code for hardcoded secrets or API tokens."""
        leaks = []
        status = self.get_git_status()
        files_to_check = [m["file"] for m in status.get("modified_files", [])]

        for rel_file in files_to_check:
            p = REPO_ROOT / rel_file
            if not p.exists() or not p.is_file():
                continue
            if p.suffix.lower() in [".png", ".jpg", ".webp", ".ico", ".exe", ".dll", ".db", ".sqlite", ".bin"]:
                continue

            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern, leak_type in LEAK_PATTERNS:
                        if pattern.search(line):
                            leaks.append({
                                "file": rel_file,
                                "line": line_num,
                                "leak_type": leak_type,
                                "preview": line[:80].strip()
                            })
            except Exception:
                pass

        return {
            "clean": len(leaks) == 0,
            "total_leaks": len(leaks),
            "files_scanned": len(files_to_check),
            "leaks": leaks
        }

    # -------------------------------------------------------------
    # 4. Patch Proposal & Safe Review System
    # -------------------------------------------------------------
    def get_patch_proposals(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM patch_proposals ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def create_patch_proposal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        file_path = data.get("file_path", "").strip()
        description = data.get("description", "").strip()
        old_text = data.get("old_text", "")
        new_text = data.get("new_text", "")
        target_env = data.get("target_env", "local")
        author = data.get("author", "Antony / Cali")

        if not file_path or not old_text:
            return {"ok": False, "error": "file_path and old_text are required"}

        with self._get_connection() as conn:
            cur = conn.execute("""
                INSERT INTO patch_proposals (file_path, description, target_env, old_text, new_text, status, author, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (file_path, description, target_env, old_text, new_text, author, time.time()))
            proposal_id = cur.lastrowid

        return {"ok": True, "id": proposal_id, "message": f"Patch proposal #{proposal_id} created for '{file_path}'"}

    def apply_patch(self, proposal_id: int) -> Dict[str, Any]:
        """Safely applies a reviewed patch proposal to the target file."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM patch_proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row:
                return {"ok": False, "error": f"Proposal #{proposal_id} not found"}
            p_data = dict(row)

            target_file = REPO_ROOT / p_data["file_path"]
            if not target_file.exists():
                return {"ok": False, "error": f"Target file '{p_data['file_path']}' does not exist on disk"}

            content = target_file.read_text(encoding="utf-8")
            if p_data["old_text"] not in content:
                return {"ok": False, "error": "Target string not found in target file. It may have already been modified."}

            updated_content = content.replace(p_data["old_text"], p_data["new_text"], 1)
            target_file.write_text(updated_content, encoding="utf-8")

            # Update proposal status
            conn.execute("UPDATE patch_proposals SET status='applied', applied_at=? WHERE id=?", (time.time(), proposal_id))

            # Record deployment receipt
            conn.execute("""
                INSERT INTO deployment_receipts (release_tag, action, file_path, status, details, timestamp)
                VALUES (?, 'patch_applied', ?, 'SUCCESS', ?, ?)
            """, (f"PATCH-{proposal_id}", p_data["file_path"], p_data["description"], time.time()))

        return {"ok": True, "message": f"Successfully applied patch #{proposal_id} to '{p_data['file_path']}'!"}

    def reject_patch(self, proposal_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.execute("UPDATE patch_proposals SET status='rejected' WHERE id=?", (proposal_id,))
        return {"ok": True, "message": f"Patch #{proposal_id} rejected."}

    def get_deployment_receipts(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM deployment_receipts ORDER BY id DESC LIMIT 30").fetchall()
            return [dict(r) for r in rows]


# Singleton instance
DEV = DevEngine()

