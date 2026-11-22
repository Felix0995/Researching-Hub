"""Phase 0 quality validation tests for ResearchHub MBA V1.0.

Tests module imports, configuration integrity, governance file existence,
and .gitignore security rules.
"""

from __future__ import annotations

from pathlib import Path

import researchhub
from researchhub import __app_name__, __version__
from researchhub.config import AppConfig, config


def test_package_metadata() -> None:
    """Verify package name and version are set correctly."""
    assert __app_name__ == "ResearchHub MBA"
    assert __version__ == "0.1.0"
    assert hasattr(researchhub, "__version__")


def test_package_submodules_importable() -> None:
    """Verify that all core submodules can be imported cleanly."""
    import researchhub.db
    import researchhub.models
    import researchhub.parsers
    import researchhub.repositories
    import researchhub.services
    import researchhub.storage
    import researchhub.ui

    assert researchhub.ui is not None
    assert researchhub.services is not None
    assert researchhub.repositories is not None
    assert researchhub.parsers is not None
    assert researchhub.storage is not None
    assert researchhub.db is not None
    assert researchhub.models is not None


def test_app_config_defaults() -> None:
    """Verify default application configuration values."""
    assert config.host == "127.0.0.1"
    assert config.port == 8501
    assert config.default_language == "vi"
    assert config.project_root.is_dir()
    # Ensure no hard-coded machine usernames in relative-derived root
    assert (config.project_root / "researchhub").is_dir()


def test_app_config_custom_root(tmp_path: Path) -> None:
    """Verify AppConfig computes all paths relative to a given root."""
    custom_cfg = AppConfig.load(root_dir=tmp_path)
    assert custom_cfg.project_root == tmp_path
    assert custom_cfg.data_dir == tmp_path / "data"
    assert custom_cfg.storage_dir == tmp_path / "data" / "storage"
    assert custom_cfg.database_path == tmp_path / "data" / "researchhub.sqlite"
    assert custom_cfg.backup_dir == tmp_path / "data" / "backups"


def test_governance_files_present() -> None:
    """Verify that mandatory governance files exist in project root."""
    root = config.project_root
    for fname in ["AGENTS.md", "agent.md", "gdd.md"]:
        fpath = root / fname
        assert fpath.is_file(), f"Missing required governance file: {fname}"
        assert fpath.stat().st_size > 0, f"Governance file {fname} is empty"


def test_gitignore_contains_critical_rules() -> None:
    """Verify .gitignore protects sensitive user data, databases, and secrets."""
    gitignore_path = config.project_root / ".gitignore"
    assert gitignore_path.is_file(), "Missing .gitignore file"

    content = gitignore_path.read_text(encoding="utf-8")
    critical_rules = [
        ".venv/",
        "data/",
        "*.sqlite",
        "*.db",
        ".env",
    ]
    for rule in critical_rules:
        assert rule in content, f".gitignore missing critical rule: {rule}"


def test_entrypoint_syntax_and_import() -> None:
    """Verify that app.py is syntactically valid and importable."""
    import app

    assert hasattr(app, "main")
    assert callable(app.main)
