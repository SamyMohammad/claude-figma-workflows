"""A process-safe ledger for observed MCP call budgets."""

import sqlite3
from contextlib import closing
from pathlib import Path

from .errors import CoreError


def _connect(db: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db, timeout=30, isolation_level=None)
    connection.execute("PRAGMA busy_timeout=30000")
    connection.execute("""CREATE TABLE IF NOT EXISTS reservations (
        request_id TEXT PRIMARY KEY,
        window_id TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('reserved','sent'))
    )""")
    return connection


def reserve(db: Path, window_id: str, limit: int, request_id: str) -> bool:
    if not window_id or not request_id or limit < 0:
        raise CoreError("BUDGET_INVALID", "Window, request ID, and limit are required")
    with closing(_connect(db)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT window_id, state FROM reservations WHERE request_id=?",
                                 (request_id,)).fetchone()
        if row:
            if row[0] != window_id:
                raise CoreError("BUDGET_CONFLICT", "Request ID belongs to another window")
            return row[1] == "reserved"
        spent = connection.execute("SELECT COUNT(*) FROM reservations WHERE window_id=?",
                                   (window_id,)).fetchone()[0]
        if spent >= limit:
            return False
        connection.execute("INSERT INTO reservations VALUES (?, ?, 'reserved')",
                           (request_id, window_id))
        return True


def mark_sent(db: Path, request_id: str) -> None:
    with closing(_connect(db)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            "UPDATE reservations SET state='sent' WHERE request_id=? AND state='reserved'",
            (request_id,))
        if cursor.rowcount != 1:
            raise CoreError("BUDGET_NOT_RESERVED", "Request is missing or already sent")
