"""Persistent, bounded correction attempts."""

import re
import sqlite3
from pathlib import Path

from .errors import CoreError


def next_correction(completed: int) -> int:
    if isinstance(completed, bool) or not isinstance(completed, int) or completed < 0:
        raise CoreError("ITERATION_INVALID", "Invalid correction count")
    if completed >= 4:
        raise CoreError("ITERATION_LIMIT", "Maximum of four corrections reached")
    return completed + 1


def record_correction(path: Path, node_id: str, reference_hash: str, policy_hash: str) -> int:
    """Reserve one correction in a durable ledger; callers must retain this file."""
    if (not node_id or not all(re.fullmatch(r"[0-9a-f]{64}", value)
                               for value in (reference_hash, policy_hash))):
        raise CoreError("ITERATION_INVALID", "Invalid correction identity")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(path, timeout=30) as database:
            database.execute("CREATE TABLE IF NOT EXISTS corrections ("
                             "node_id TEXT NOT NULL, reference_hash TEXT NOT NULL, "
                             "policy_hash TEXT NOT NULL, completed INTEGER NOT NULL, "
                             "PRIMARY KEY (node_id, reference_hash, policy_hash))")
            database.execute("BEGIN IMMEDIATE")
            row = database.execute(
                "SELECT completed FROM corrections WHERE node_id=? AND reference_hash=? AND policy_hash=?",
                (node_id, reference_hash, policy_hash),
            ).fetchone()
            count = next_correction(row[0] if row else 0)
            database.execute(
                "INSERT INTO corrections VALUES (?, ?, ?, ?) ON CONFLICT(node_id, reference_hash, policy_hash) "
                "DO UPDATE SET completed=excluded.completed",
                (node_id, reference_hash, policy_hash, count),
            )
            database.commit()
            return count
    except sqlite3.Error as error:
        raise CoreError("ITERATION_INVALID", "Cannot update correction ledger") from error
