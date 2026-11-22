"""SQLite database connection and schema management for ResearchHub MBA."""

from researchhub.db.connection import get_connection, transaction
from researchhub.db.manager import (
    check_integrity,
    get_schema_version,
    get_table_names,
    init_db,
    rebuild_fts_index,
)
from researchhub.db.schema import EXPECTED_TABLES, SCHEMA_VERSION

__all__ = [
    "get_connection",
    "transaction",
    "init_db",
    "check_integrity",
    "get_schema_version",
    "get_table_names",
    "rebuild_fts_index",
    "SCHEMA_VERSION",
    "EXPECTED_TABLES",
]
