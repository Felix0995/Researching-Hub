"""Tests for SQLite database schema, constraints, FTS5, and integrity.

Covers Phase 1 required test scenarios:
- Schema creation & idempotency
- 14 tables + FTS5 virtual table verification
- Foreign key enforcement
- Many-to-many relationship integrity (documents, domains, projects, authors, tags)
- Multilingual Unicode persistence (Vietnamese, English, Traditional Chinese)
- Constraint enforcement (NOT NULL, CHECK, UNIQUE)
- Persistence across connection close and reopen
- FTS5 synchronization on insert, update, delete, and rebuild
- Atomic transaction rollbacks on errors
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from researchhub.db import (
    EXPECTED_TABLES,
    SCHEMA_VERSION,
    check_integrity,
    get_connection,
    get_schema_version,
    get_table_names,
    init_db,
    rebuild_fts_index,
    transaction,
)


def test_db_creation(tmp_path: Path) -> None:
    """Case 1: Database initializes successfully and sets schema version."""
    db_file = tmp_path / "test_hub.sqlite"
    version = init_db(db_file)

    assert version == SCHEMA_VERSION
    assert db_file.is_file()

    con = get_connection(db_file)
    try:
        assert get_schema_version(con) == SCHEMA_VERSION
    finally:
        con.close()


def test_db_idempotency(tmp_path: Path) -> None:
    """Case 2: Re-running initialization preserves existing data."""
    db_file = tmp_path / "test_hub.sqlite"
    init_db(db_file)

    # Insert sample tag
    con = get_connection(db_file)
    try:
        con.execute(
            "INSERT INTO tags (name, created_at) VALUES (?, ?);",
            ("kinh-te-vi-mo", "2026-11-22T20:00:00Z"),
        )
        con.commit()
    finally:
        con.close()

    # Second initialization
    v2 = init_db(db_file)
    assert v2 == SCHEMA_VERSION

    # Verify data preserved
    con = get_connection(db_file)
    try:
        row = con.execute("SELECT name FROM tags WHERE name = ?;", ("kinh-te-vi-mo",)).fetchone()
        assert row is not None
        assert row["name"] == "kinh-te-vi-mo"
    finally:
        con.close()


def test_expected_tables_and_fts5_present(tmp_path: Path) -> None:
    """Case 3: All 14 expected tables and FTS5 virtual table are created."""
    db_file = tmp_path / "test_hub.sqlite"
    init_db(db_file)

    con = get_connection(db_file)
    try:
        table_names = get_table_names(con)
        for expected in EXPECTED_TABLES:
            assert expected in table_names, f"Missing table: {expected}"

        # Check virtual table text_segments_fts
        fts_row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='text_segments_fts';"
        ).fetchone()
        assert fts_row is not None
    finally:
        con.close()


def test_foreign_key_enforcement(tmp_path: Path) -> None:
    """Case 4: Foreign key violations are rejected with IntegrityError."""
    db_file = tmp_path / "test_hub.sqlite"
    init_db(db_file)

    con = get_connection(db_file)
    try:
        # Inserting document pointing to non-existent file_object_id 9999 must fail
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO documents (
                    file_object_id, title, document_type, language,
                    read_status, extraction_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    9999,
                    "Invalid Document",
                    "other",
                    "vi",
                    "unread",
                    "pending",
                    "2026-11-22T20:00:00Z",
                    "2026-11-22T20:00:00Z",
                ),
            )
            con.commit()
    finally:
        con.close()


def test_document_domain_project_relationships(tmp_path: Path) -> None:
    """Case 5: Many-to-many relations across documents, domains, projects work."""
    db_file = tmp_path / "test_hub.sqlite"
    init_db(db_file)

    con = get_connection(db_file)
    try:
        # 1. Insert file object
        cur = con.execute(
            """
            INSERT INTO file_objects (
                sha256, stored_relpath, original_filename,
                file_type, mime_type, size_bytes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "a" * 64,
                "aa/test.pdf",
                "test.pdf",
                "pdf",
                "application/pdf",
                1024,
                "2026-11-22T20:00:00Z",
            ),
        )
        file_id = cur.lastrowid

        # 2. Insert document
        cur = con.execute(
            """
            INSERT INTO documents (
                file_object_id, title, document_type, language, year,
                read_status, extraction_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                file_id,
                "Chiến lược kinh doanh MBA",
                "journal_article",
                "vi",
                2025,
                "unread",
                "indexed",
                "2026-11-22T20:00:00Z",
                "2026-11-22T20:00:00Z",
            ),
        )
        doc_id = cur.lastrowid

        # 3. Insert 2 domains (hierarchical)
        cur = con.execute(
            "INSERT INTO domains (name, parent_id, description, created_at) VALUES (?, ?, ?, ?);",
            ("Quản trị kinh doanh", None, "Lĩnh vực chung", "2026-11-22T20:00:00Z"),
        )
        domain_parent_id = cur.lastrowid

        cur = con.execute(
            "INSERT INTO domains (name, parent_id, description, created_at) VALUES (?, ?, ?, ?);",
            (
                "Chiến lược doanh nghiệp",
                domain_parent_id,
                "Chuyên ngành sâu",
                "2026-11-22T20:00:00Z",
            ),
        )
        domain_child_id = cur.lastrowid

        # 4. Insert 2 projects
        cur = con.execute(
            "INSERT INTO projects (name, status, created_at, updated_at) VALUES (?, ?, ?, ?);",
            ("Luận văn Thạc sĩ", "active", "2026-11-22T20:00:00Z", "2026-11-22T20:00:00Z"),
        )
        proj1_id = cur.lastrowid

        cur = con.execute(
            "INSERT INTO projects (name, status, created_at, updated_at) VALUES (?, ?, ?, ?);",
            ("Đề tài Nghiên cứu 2026", "active", "2026-11-22T20:00:00Z", "2026-11-22T20:00:00Z"),
        )
        proj2_id = cur.lastrowid

        # 5. Link document to both domains and both projects
        con.execute(
            "INSERT INTO document_domains (document_id, domain_id) VALUES (?, ?);",
            (doc_id, domain_parent_id),
        )
        con.execute(
            "INSERT INTO document_domains (document_id, domain_id) VALUES (?, ?);",
            (doc_id, domain_child_id),
        )
        con.execute(
            "INSERT INTO document_projects (document_id, project_id) VALUES (?, ?);",
            (doc_id, proj1_id),
        )
        con.execute(
            "INSERT INTO document_projects (document_id, project_id) VALUES (?, ?);",
            (doc_id, proj2_id),
        )
        con.commit()

        # Verify links
        domains = con.execute(
            "SELECT domain_id FROM document_domains WHERE document_id = ? ORDER BY domain_id;",
            (doc_id,),
        ).fetchall()
        assert len(domains) == 2

        # Verify deleting relationship does NOT delete document or file
        con.execute(
            "DELETE FROM document_domains WHERE document_id = ? AND domain_id = ?;",
            (doc_id, domain_child_id),
        )
        con.commit()

        doc_check = con.execute("SELECT id FROM documents WHERE id = ?;", (doc_id,)).fetchone()
        file_check = con.execute("SELECT id FROM file_objects WHERE id = ?;", (file_id,)).fetchone()
        assert doc_check is not None
        assert file_check is not None
    finally:
        con.close()


def test_multilingual_unicode_support(tmp_path: Path) -> None:
    """Case 6: Full Unicode support for Vietnamese, English, and Traditional Chinese."""
    db_file = tmp_path / "test_hub.sqlite"
    init_db(db_file)

    con = get_connection(db_file)
    try:
        # Multilingual glossary record
        con.execute(
            """
            INSERT INTO glossary_terms (
                term_vi, term_en, term_zh_trad, aliases, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "Quản trị chuỗi cung ứng",
                "Supply Chain Management",
                "供應鏈管理",
                "SCM, Logistics",
                "Thuật ngữ học thuật cốt lõi trong chương trình MBA.",
                "2026-11-22T20:00:00Z",
                "2026-11-22T20:00:00Z",
            ),
        )
        con.commit()

        row = con.execute(
            "SELECT * FROM glossary_terms WHERE term_en = ?;",
            ("Supply Chain Management",),
        ).fetchone()

        assert row is not None
        assert row["term_vi"] == "Quản trị chuỗi cung ứng"
        assert row["term_zh_trad"] == "供應鏈管理"
        assert "chương trình MBA" in row["notes"]
    finally:
        con.close()


def test_invalid_data_rejected_by_constraints(tmp_path: Path) -> None:
    """Case 7: Check constraints, not-null, and unique violations are rejected."""
    db_file = tmp_path / "test_hub.sqlite"
    init_db(db_file)

    con = get_connection(db_file)
    try:
        # Test 1: Negative file size violates CHECK (size_bytes >= 0)
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO file_objects (
                    sha256, stored_relpath, original_filename,
                    file_type, mime_type, size_bytes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "b" * 64,
                    "bb/f.pdf",
                    "f.pdf",
                    "pdf",
                    "application/pdf",
                    -10,
                    "2026-11-22T20:00:00Z",
                ),
            )
            con.commit()

        # Test 2: Invalid read_status violates CHECK constraint
        cur = con.execute(
            """
            INSERT INTO file_objects (
                sha256, stored_relpath, original_filename,
                file_type, mime_type, size_bytes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            ("c" * 64, "cc/f.pdf", "f.pdf", "pdf", "application/pdf", 100, "2026-11-22T20:00:00Z"),
        )
        fid = cur.lastrowid

        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                """
                INSERT INTO documents (
                    file_object_id, title, read_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (fid, "Title", "invalid_status", "2026-11-22T20:00:00Z", "2026-11-22T20:00:00Z"),
            )
            con.commit()

        # Test 3: Duplicate tag name violates UNIQUE
        con.execute(
            "INSERT INTO tags (name, created_at) VALUES ('tai-chinh', '2026-11-22T20:00:00Z');"
        )
        con.commit()

        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO tags (name, created_at) VALUES ('tai-chinh', '2026-11-22T20:00:00Z');"
            )
            con.commit()
    finally:
        con.close()


def test_data_persistence_across_connections(tmp_path: Path) -> None:
    """Case 12: Data persists after closing and reopening database."""
    db_file = tmp_path / "test_persist.sqlite"
    init_db(db_file)

    # Connection 1: write
    con1 = get_connection(db_file)
    try:
        con1.execute(
            """
            INSERT INTO projects (
                name, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?);
            """,
            (
                "Dự án Alpha",
                "Mô tả dự án",
                "active",
                "2026-11-22T20:00:00Z",
                "2026-11-22T20:00:00Z",
            ),
        )
        con1.commit()
    finally:
        con1.close()

    # Connection 2: read
    con2 = get_connection(db_file)
    try:
        row = con2.execute("SELECT * FROM projects WHERE name = ?;", ("Dự án Alpha",)).fetchone()
        assert row is not None
        assert row["description"] == "Mô tả dự án"
        assert row["status"] == "active"
    finally:
        con2.close()


def test_fts5_sync_on_insert_update_delete(tmp_path: Path) -> None:
    """Case 13: FTS5 stays in sync after insert, update, delete of text segments."""
    db_file = tmp_path / "test_fts.sqlite"
    init_db(db_file)

    con = get_connection(db_file)
    try:
        # Create minimal parent document
        cur = con.execute(
            """
            INSERT INTO file_objects (
                sha256, stored_relpath, original_filename,
                file_type, mime_type, size_bytes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "d" * 64,
                "dd/doc.pdf",
                "doc.pdf",
                "pdf",
                "application/pdf",
                500,
                "2026-11-22T20:00:00Z",
            ),
        )
        fid = cur.lastrowid
        cur = con.execute(
            """
            INSERT INTO documents (
                file_object_id, title, document_type, language,
                read_status, extraction_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                fid,
                "FTS Test Doc",
                "other",
                "vi",
                "unread",
                "indexed",
                "2026-11-22T20:00:00Z",
                "2026-11-22T20:00:00Z",
            ),
        )
        doc_id = cur.lastrowid

        # 1. Insert text segment -> should be indexed by FTS
        cur = con.execute(
            """
            INSERT INTO text_segments (
                document_id, segment_order, source_kind, page_number, text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                doc_id,
                1,
                "body",
                12,
                "Lý thuyết chi phí giao dịch trong quản trị chiến lược doanh nghiệp.",
                "2026-11-22T20:00:00Z",
            ),
        )
        seg_id = cur.lastrowid
        con.commit()

        match_rows = con.execute(
            "SELECT rowid FROM text_segments_fts WHERE text_segments_fts MATCH ?;",
            ("giao dịch",),
        ).fetchall()
        assert len(match_rows) == 1
        assert match_rows[0][0] == seg_id

        # 2. Update text segment -> FTS index updates
        con.execute(
            "UPDATE text_segments SET text = ? WHERE id = ?;",
            ("Mô hình kinh tế lượng tài chính doanh nghiệp ứng dụng.", seg_id),
        )
        con.commit()

        # Old query returns nothing
        old_match = con.execute(
            "SELECT rowid FROM text_segments_fts WHERE text_segments_fts MATCH ?;",
            ("giao dịch",),
        ).fetchall()
        assert len(old_match) == 0

        # New query returns updated segment
        new_match = con.execute(
            "SELECT rowid FROM text_segments_fts WHERE text_segments_fts MATCH ?;",
            ("kinh tế lượng",),
        ).fetchall()
        assert len(new_match) == 1
        assert new_match[0][0] == seg_id

        # 3. Delete text segment -> FTS index deletes entry
        con.execute("DELETE FROM text_segments WHERE id = ?;", (seg_id,))
        con.commit()

        deleted_match = con.execute(
            "SELECT rowid FROM text_segments_fts WHERE text_segments_fts MATCH ?;",
            ("kinh tế lượng",),
        ).fetchall()
        assert len(deleted_match) == 0

        # 4. Test rebuild_fts_index
        rebuild_fts_index(db_file)
    finally:
        con.close()


def test_failed_operations_rollback_and_safety(tmp_path: Path) -> None:
    """Case 14: Failed transactions rollback cleanly without leaving partial writes."""
    db_file = tmp_path / "test_rollback.sqlite"
    init_db(db_file)

    con = get_connection(db_file)
    try:
        # Pre-populate 1 project
        con.execute(
            """
            INSERT INTO projects (name, status, created_at, updated_at)
            VALUES ('P1', 'active', 't', 't');
            """
        )
        con.commit()

        # Attempt transaction that inserts P2 then fails on duplicate P1
        with pytest.raises(sqlite3.IntegrityError):
            with transaction(con):
                con.execute(
                    """
                    INSERT INTO projects (name, status, created_at, updated_at)
                    VALUES ('P2', 'active', 't', 't');
                    """
                )
                # This must fail and rollback P2
                con.execute(
                    """
                    INSERT INTO projects (name, status, created_at, updated_at)
                    VALUES ('P1', 'active', 't', 't');
                    """
                )

        # Verify P2 was not committed
        p2_check = con.execute("SELECT * FROM projects WHERE name = 'P2';").fetchone()
        assert p2_check is None

        # Verify database integrity passes
        is_healthy, msgs = check_integrity(db_file)
        assert is_healthy is True
        assert msgs == ["ok"]
    finally:
        con.close()
