"""Database initialization, migration, and maintenance manager.

Handles idempotent schema setup, version checks, integrity checks,
and FTS5 index rebuilds without external ORM dependencies.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple, Union

from researchhub.config import config
from researchhub.db.connection import get_connection, transaction
from researchhub.db.schema import DDL_STATEMENTS, SCHEMA_VERSION

logger = logging.getLogger(__name__)

PathLike = Union[Path, str]


class DatabaseError(Exception):
    """Base exception for database errors."""


class SchemaMigrationError(DatabaseError):
    """Raised when the database schema version is incompatible and requires migration."""


def init_db(db_path: PathLike | None = None) -> int:
    """Initialize database schema idempotently.

    - Creates directory if file-based and does not exist.
    - If user_version == 0, executes full DDL and sets user_version to SCHEMA_VERSION.
    - If user_version == SCHEMA_VERSION, preserves existing data and returns.
    - Never deletes or resets existing database tables.
    - If schema version does not match, raises SchemaMigrationError and preserves data.
    """
    if db_path is None:
        target_path: PathLike = config.database_path
    else:
        target_path = db_path

    # Ensure parent directory exists for file-based DB
    if isinstance(target_path, Path):
        target_path.parent.mkdir(parents=True, exist_ok=True)
    elif (
        isinstance(target_path, str)
        and target_path != ":memory:"
        and not target_path.startswith("file:")
    ):
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)

    con = get_connection(target_path)
    try:
        current_version = get_schema_version(con)

        if current_version == 0:
            logger.info(
                "Initializing fresh schema version %d at %s",
                SCHEMA_VERSION,
                target_path,
            )
            with transaction(con):
                for statement in DDL_STATEMENTS:
                    con.execute(statement)
                con.execute(f"PRAGMA user_version = {SCHEMA_VERSION};")
            return SCHEMA_VERSION

        if current_version == SCHEMA_VERSION:
            logger.info(
                "Database schema at %s is up-to-date (version %d)",
                target_path,
                current_version,
            )
            return current_version

        if current_version < SCHEMA_VERSION:
            raise SchemaMigrationError(
                f"Database schema at {target_path} is version {current_version}, "
                f"which is older than application schema version {SCHEMA_VERSION}. "
                "No automated migration is registered for this version. "
                "The database has been left unmodified to prevent data loss."
            )

        raise SchemaMigrationError(
            f"Database schema at {target_path} is version {current_version}, "
            f"which is newer than application schema version {SCHEMA_VERSION}. "
            "Please update the application."
        )
    finally:
        con.close()


def get_schema_version(con) -> int:
    """Return the PRAGMA user_version of the given database connection."""
    row = con.execute("PRAGMA user_version;").fetchone()
    return int(row[0]) if row else 0


def check_integrity(db_path: PathLike | None = None) -> Tuple[bool, List[str]]:
    """Verify relational integrity and physical database consistency.

    Runs:
    - PRAGMA integrity_check;
    - PRAGMA foreign_key_check;

    Returns (is_healthy, messages).
    """
    con = get_connection(db_path)
    messages: List[str] = []
    is_healthy = True

    try:
        # 1. Physical / B-Tree integrity check
        cursor = con.execute("PRAGMA integrity_check;")
        rows = cursor.fetchall()
        for r in rows:
            val = str(r[0])
            if val != "ok":
                is_healthy = False
                messages.append(f"Integrity check issue: {val}")

        # 2. Foreign key consistency check
        fk_cursor = con.execute("PRAGMA foreign_key_check;")
        fk_violations = fk_cursor.fetchall()
        if fk_violations:
            is_healthy = False
            for v in fk_violations:
                messages.append(
                    f"Foreign key violation: table={v[0]}, rowid={v[1]}, target={v[2]}, fkid={v[3]}"
                )

        if is_healthy:
            messages.append("ok")

        return is_healthy, messages
    finally:
        con.close()


def rebuild_fts_index(db_path: PathLike | None = None) -> None:
    """Rebuild the SQLite FTS5 full-text index from text_segments table."""
    con = get_connection(db_path)
    try:
        with transaction(con):
            con.execute("INSERT INTO text_segments_fts(text_segments_fts) VALUES('rebuild');")
        logger.info("FTS5 index rebuilt successfully.")
    finally:
        con.close()


def get_table_names(con) -> List[str]:
    """Return sorted list of user table names in the database."""
    cursor = con.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
          AND name NOT LIKE 'text_segments_fts_%'
        ORDER BY name;
        """
    )
    return [row[0] for row in cursor.fetchall()]
