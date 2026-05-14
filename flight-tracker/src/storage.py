"""SQLite persistence for price history and notification state."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_name    TEXT NOT NULL,
    checked_at    TEXT NOT NULL,
    price         REAL NOT NULL,
    airline       TEXT,
    flight_number TEXT,
    departure     TEXT,
    arrival       TEXT,
    duration_min  INTEGER
);
CREATE INDEX IF NOT EXISTS idx_price_history_watch ON price_history(watch_name);

CREATE TABLE IF NOT EXISTS notifications (
    watch_name        TEXT PRIMARY KEY,
    last_notified_at  TEXT NOT NULL,
    last_price        REAL NOT NULL
);
"""


class Storage:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def record_price(
        self,
        watch_name: str,
        price: float,
        airline: str | None = None,
        flight_number: str | None = None,
        departure: str | None = None,
        arrival: str | None = None,
        duration_min: int | None = None,
    ) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO price_history
                (watch_name, checked_at, price, airline, flight_number, departure, arrival, duration_min)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    watch_name,
                    datetime.now(timezone.utc).isoformat(),
                    price,
                    airline,
                    flight_number,
                    departure,
                    arrival,
                    duration_min,
                ),
            )

    def min_price(self, watch_name: str) -> float | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT MIN(price) AS m FROM price_history WHERE watch_name = ?",
                (watch_name,),
            ).fetchone()
            return row["m"] if row and row["m"] is not None else None

    def last_notification(self, watch_name: str) -> tuple[float, str] | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT last_price, last_notified_at FROM notifications WHERE watch_name = ?",
                (watch_name,),
            ).fetchone()
            return (row["last_price"], row["last_notified_at"]) if row else None

    def mark_notified(self, watch_name: str, price: float) -> None:
        with self._conn() as c:
            c.execute(
                """INSERT INTO notifications (watch_name, last_notified_at, last_price)
                VALUES (?, ?, ?)
                ON CONFLICT(watch_name) DO UPDATE SET
                    last_notified_at = excluded.last_notified_at,
                    last_price = excluded.last_price""",
                (watch_name, datetime.now(timezone.utc).isoformat(), price),
            )
