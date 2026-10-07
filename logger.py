"""
logger.py — Middleware that records every agent tool call to SQLite.

Keys events on agent_identity (a stable name like 'support-agent-v3'),
NOT on ephemeral container/pod IDs, to avoid the identity gap described
in the project proposal.

Owner: Member 1
"""

import sqlite3
import json
import time
from typing import List, Tuple, Optional


class EventLogger:
    """SQLite-backed event logger for agent tool calls."""

    def __init__(self, db_path: str = "events.db"):
        """Initialize the logger and create the events table if needed.

        Args:
            db_path: path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          REAL    NOT NULL,
                task_id     TEXT    NOT NULL,
                agent_identity TEXT NOT NULL,
                tool        TEXT    NOT NULL,
                params      TEXT    NOT NULL,
                result      TEXT
            )
        """)
        self.conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def log_event(self, task_id: str, agent_identity: str, tool: str,
                  params: dict, result: str) -> int:
        """Record a single tool-call event.

        Args:
            task_id:        unique identifier for the current task/session.
            agent_identity: stable agent name (e.g. 'support-agent-v3').
            tool:           name of the tool that was called.
            params:         dictionary of parameters passed to the tool.
            result:         string result returned by the tool (truncated to 500 chars).

        Returns:
            The SQLite row ID of the inserted event.
        """
        cursor = self.conn.execute(
            "INSERT INTO events (ts, task_id, agent_identity, tool, params, result) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (time.time(), task_id, agent_identity, tool,
             json.dumps(params), str(result)[:500])
        )
        self.conn.commit()
        return cursor.lastrowid

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def recent_events(self, agent_identity: str,
                      limit: int = 10) -> List[Tuple]:
        """Get the most recent events for a given agent identity.

        Returns:
            List of (ts, tool, params) tuples, **newest first**.
        """
        cur = self.conn.execute(
            "SELECT ts, tool, params FROM events "
            "WHERE agent_identity = ? ORDER BY id DESC LIMIT ?",
            (agent_identity, limit)
        )
        return cur.fetchall()

    def get_events_by_task(self, task_id: str) -> List[Tuple]:
        """Get all events for a specific task, ordered chronologically.

        Returns:
            List of (id, ts, agent_identity, tool, params, result) tuples.
        """
        cur = self.conn.execute(
            "SELECT id, ts, agent_identity, tool, params, result FROM events "
            "WHERE task_id = ? ORDER BY id ASC",
            (task_id,)
        )
        return cur.fetchall()

    def get_all_events(self, limit: int = 100) -> List[Tuple]:
        """Get all events across all tasks (for reporting), newest first.

        Returns:
            List of (id, ts, task_id, agent_identity, tool, params, result) tuples.
        """
        cur = self.conn.execute(
            "SELECT id, ts, task_id, agent_identity, tool, params, result "
            "FROM events ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return cur.fetchall()

    def count_events(self, agent_identity: Optional[str] = None) -> int:
        """Count total events, optionally filtered by agent identity."""
        if agent_identity:
            cur = self.conn.execute(
                "SELECT COUNT(*) FROM events WHERE agent_identity = ?",
                (agent_identity,)
            )
        else:
            cur = self.conn.execute("SELECT COUNT(*) FROM events")
        return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self):
        """Delete all events (useful for testing and demo resets)."""
        self.conn.execute("DELETE FROM events")
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
