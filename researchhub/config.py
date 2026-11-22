"""Application configuration for ResearchHub MBA V1.0.

Centralizes paths, runtime constants, and environment variables.
Prevents hard-coded absolute paths and machine-specific user home directories.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""

    # Project paths
    project_root: Path
    data_dir: Path
    storage_dir: Path
    database_path: Path
    backup_dir: Path

    # Network / Bind
    host: str = "127.0.0.1"
    port: int = 8501

    # App meta
    app_name: str = "ResearchHub MBA"
    version: str = "0.1.0"
    default_language: str = "vi"

    @classmethod
    def load(cls, root_dir: Path | None = None) -> AppConfig:
        """Load configuration relative to the project root directory."""
        if root_dir is None:
            # Resolves to repo root (two levels up from researchhub/config.py)
            root_dir = Path(__file__).resolve().parent.parent

        data_dir_name = os.getenv("DATA_DIR", "data")
        data_dir = (root_dir / data_dir_name).resolve()

        storage_rel = os.getenv("STORAGE_DIR", "data/storage")
        storage_dir = (root_dir / storage_rel).resolve()

        db_rel = os.getenv("DATABASE_PATH", "data/researchhub.sqlite")
        database_path = (root_dir / db_rel).resolve()

        backup_rel = os.getenv("BACKUP_DIR", "data/backups")
        backup_dir = (root_dir / backup_rel).resolve()

        host = os.getenv("APP_HOST", "127.0.0.1")
        port_raw = os.getenv("APP_PORT", "8501")
        try:
            port = int(port_raw)
        except ValueError:
            port = 8501

        return cls(
            project_root=root_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            database_path=database_path,
            backup_dir=backup_dir,
            host=host,
            port=port,
        )


# Global default configuration instance
config = AppConfig.load()
