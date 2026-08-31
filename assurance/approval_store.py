"""WS4-2: SQLite-backed approval store for HUMAN_REVIEW items.

Cloud SQL was explicitly decided against for v0.1 (see final-22-hours-plan.md
section 3) -- a SQLite file gives an equivalent cross-process persistence
proof without the IAM/networking setup cost.
"""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/approvals.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    assessment_id TEXT PRIMARY KEY,
    risk_tier     TEXT NOT NULL,
    route         TEXT NOT NULL,
    policy_id     TEXT NOT NULL,
    reason        TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    decision      TEXT,
    reviewer      TEXT,
    created_at    TEXT NOT NULL,
    resolved_at   TEXT
);
"""


@contextmanager
def _connect(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def escalate(assessment_id: str, risk_tier: str, route: str,
             policy_id: str, reason: str, db_path: Path = DB_PATH) -> None:
    """Records a HUMAN_REVIEW/BLOCK item as PENDING. Called by batch.py."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO approvals "
            "(assessment_id, risk_tier, route, policy_id, reason, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'PENDING', ?)",
            (assessment_id, risk_tier, route, policy_id, reason,
             datetime.now(timezone.utc).isoformat()),
        )


def list_pending(db_path: Path = DB_PATH) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE status = 'PENDING' ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]


def resolve(assessment_id: str, decision: str, reviewer: str,
            db_path: Path = DB_PATH) -> dict:
    """decision: APPROVE or REJECT. Returns the resolved row, or raises
    KeyError if assessment_id isn't pending."""
    if decision not in ("APPROVE", "REJECT"):
        raise ValueError(f"decision must be APPROVE or REJECT, got {decision!r}")
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM approvals WHERE assessment_id = ?", (assessment_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"no approval record for {assessment_id!r}")
        if row["status"] != "PENDING":
            raise ValueError(f"{assessment_id!r} is already {row['status']}, not PENDING")

        resolved_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE approvals SET status = ?, decision = ?, reviewer = ?, resolved_at = ? "
            "WHERE assessment_id = ?",
            (decision, decision, reviewer, resolved_at, assessment_id),
        )
        row = conn.execute(
            "SELECT * FROM approvals WHERE assessment_id = ?", (assessment_id,)
        ).fetchone()
        return dict(row)
