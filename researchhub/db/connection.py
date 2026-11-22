"""Database connection management for ResearchHub MBA V1.0.

Provides standard SQLite connection handling with enforced foreign keys,
WAL journal mode, parameterized queries, and transaction contexts.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Union

from researchhub.config import config

PathLike = Union[Path, str]


def get_connection(db_path: PathLike | None = None) -> sqlite3.Connection:
    """Open and configure a SQLite connection.

    Enforces:
    - PRAGMA foreign_keys = ON;
    - PRAGMA journal_mode = WAL; (for file-based databases)
    - PRAGMA synchronous = NORMAL;
    - con.row_factory = sqlite3.Row;
    """
    if db_path is None:
        target_path = str(config.database_path)
    else:
        target_path = str(db_path)

    # In-memory or file-based connection
    con = sqlite3.connect(target_path, timeout=30.0)
    con.row_factory = sqlite3.Row

    # Always enforce foreign keys
    con.execute("PRAGMA foreign_keys = ON;")

    # Optimization for file-based databases
    if target_path != ":memory:" and not target_path.startswith("file:"):
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA synchronous = NORMAL;")

    return con


@contextmanager
def transaction(con: sqlite3.Connection) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for atomic database transactions.

    Automatically commits if block succeeds, rollbacks on error.
    """
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
