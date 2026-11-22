"""SQLite database schema definitions and DDL scripts for ResearchHub MBA V1.0.

Defines the 14 logical tables, relational constraints, foreign keys,
indexes, and FTS5 full-text search virtual table according to GDD Section 5.
"""

from __future__ import annotations

SCHEMA_VERSION: int = 1

EXPECTED_TABLES: tuple[str, ...] = (
    "file_objects",
    "documents",
    "authors",
    "document_authors",
    "domains",
    "document_domains",
    "projects",
    "document_projects",
    "tags",
    "document_tags",
    "text_segments",
    "notes",
    "excerpts",
    "glossary_terms",
)

DDL_STATEMENTS: tuple[str, ...] = (
    # 1. file_objects: Managed physical binary files
    """
    CREATE TABLE IF NOT EXISTS file_objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sha256 TEXT NOT NULL UNIQUE,
        stored_relpath TEXT NOT NULL UNIQUE,
        original_filename TEXT NOT NULL,
        file_type TEXT NOT NULL CHECK (file_type IN ('pdf', 'docx', 'other')),
        mime_type TEXT NOT NULL,
        size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
        created_at TEXT NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_file_objects_sha256 ON file_objects(sha256);",

    # 2. documents: Document profiles
    """
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_object_id INTEGER NOT NULL UNIQUE,
        title TEXT NOT NULL,
        document_type TEXT NOT NULL DEFAULT 'other',
        language TEXT NOT NULL DEFAULT 'vi',
        year INTEGER CHECK (year IS NULL OR (year >= 1000 AND year <= 2100)),
        doi TEXT,
        abstract TEXT,
        read_status TEXT NOT NULL DEFAULT 'unread'
            CHECK (read_status IN ('unread', 'reading', 'read')),
        extraction_status TEXT NOT NULL DEFAULT 'pending'
            CHECK (extraction_status IN (
                'pending', 'processing', 'indexed', 'no_extractable_text', 'failed', 'unsupported'
            )),
        extraction_error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (file_object_id) REFERENCES file_objects(id) ON DELETE RESTRICT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_documents_file_object_id ON documents(file_object_id);",
    "CREATE INDEX IF NOT EXISTS idx_documents_year ON documents(year);",
    "CREATE INDEX IF NOT EXISTS idx_documents_language ON documents(language);",
    "CREATE INDEX IF NOT EXISTS idx_documents_read_status ON documents(read_status);",
    "CREATE INDEX IF NOT EXISTS idx_documents_extraction_status ON documents(extraction_status);",

    # 3. authors: Author library
    """
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        normalized_name TEXT,
        created_at TEXT NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_authors_full_name ON authors(full_name);",

    # 4. document_authors: N:N relationship with author ordering
    """
    CREATE TABLE IF NOT EXISTS document_authors (
        document_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        author_order INTEGER NOT NULL DEFAULT 1 CHECK (author_order >= 1),
        PRIMARY KEY (document_id, author_id),
        UNIQUE (document_id, author_order),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE RESTRICT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_document_authors_author_id ON document_authors(author_id);",

    # 5. domains: Hierarchical taxonomy
    """
    CREATE TABLE IF NOT EXISTS domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        description TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (parent_id) REFERENCES domains(id) ON DELETE SET NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_domains_parent_id ON domains(parent_id);",
    (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_domains_root_name "
        "ON domains(name) WHERE parent_id IS NULL;"
    ),
    (
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_domains_child_name "
        "ON domains(name, parent_id) WHERE parent_id IS NOT NULL;"
    ),

    # 6. document_domains: N:N relationship
    """
    CREATE TABLE IF NOT EXISTS document_domains (
        document_id INTEGER NOT NULL,
        domain_id INTEGER NOT NULL,
        PRIMARY KEY (document_id, domain_id),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE RESTRICT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_document_domains_domain_id ON document_domains(domain_id);",

    # 7. projects: Research projects
    """
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'active'
            CHECK (status IN ('active', 'completed', 'archived', 'paused')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);",

    # 8. document_projects: N:N relationship
    """
    CREATE TABLE IF NOT EXISTS document_projects (
        document_id INTEGER NOT NULL,
        project_id INTEGER NOT NULL,
        PRIMARY KEY (document_id, project_id),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_document_projects_project_id ON document_projects(project_id);",

    # 9. tags: Keyword tags
    """
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);",

    # 10. document_tags: N:N relationship
    """
    CREATE TABLE IF NOT EXISTS document_tags (
        document_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (document_id, tag_id),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE RESTRICT
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_document_tags_tag_id ON document_tags(tag_id);",

    # 11. text_segments: Extracted text segments
    """
    CREATE TABLE IF NOT EXISTS text_segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        segment_order INTEGER NOT NULL CHECK (segment_order >= 0),
        source_kind TEXT NOT NULL DEFAULT 'body'
            CHECK (source_kind IN ('title', 'abstract', 'heading', 'body', 'table', 'footnote')),
        page_number INTEGER CHECK (page_number IS NULL OR page_number >= 1),
        paragraph_number INTEGER CHECK (paragraph_number IS NULL OR paragraph_number >= 1),
        text TEXT NOT NULL,
        extraction_metadata TEXT,
        created_at TEXT NOT NULL,
        UNIQUE (document_id, segment_order),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    """,
    (
        "CREATE INDEX IF NOT EXISTS idx_text_segments_doc_order "
        "ON text_segments(document_id, segment_order);"
    ),
    "CREATE INDEX IF NOT EXISTS idx_text_segments_page ON text_segments(document_id, page_number);",

    # 12. notes: Personal research notes and manual structured academic fields
    """
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        project_id INTEGER,
        kind TEXT NOT NULL DEFAULT 'general'
            CHECK (kind IN ('general', 'methodology', 'summary', 'critique', 'idea')),
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        research_question TEXT,
        theory_framework TEXT,
        hypotheses TEXT,
        sample_context TEXT,
        method TEXT,
        variables TEXT,
        findings TEXT,
        limitations TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_notes_document_id ON notes(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_notes_project_id ON notes(project_id);",
    "CREATE INDEX IF NOT EXISTS idx_notes_kind ON notes(kind);",

    # 13. excerpts: Verbatim quotes linked to source locations
    """
    CREATE TABLE IF NOT EXISTS excerpts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        text_segment_id INTEGER,
        page_number INTEGER CHECK (page_number IS NULL OR page_number >= 1),
        paragraph_number INTEGER CHECK (paragraph_number IS NULL OR paragraph_number >= 1),
        exact_quote TEXT NOT NULL,
        comment TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (text_segment_id) REFERENCES text_segments(id) ON DELETE SET NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_excerpts_document_id ON excerpts(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_excerpts_text_segment_id ON excerpts(text_segment_id);",

    # 14. glossary_terms: Multilingual glossary
    """
    CREATE TABLE IF NOT EXISTS glossary_terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        term_vi TEXT NOT NULL,
        term_en TEXT NOT NULL,
        term_zh_trad TEXT,
        aliases TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (term_vi, term_en)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_glossary_term_vi ON glossary_terms(term_vi);",
    "CREATE INDEX IF NOT EXISTS idx_glossary_term_en ON glossary_terms(term_en);",

    # 15. Virtual FTS5 table and synchronization triggers
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS text_segments_fts USING fts5(
        text,
        content='text_segments',
        content_rowid='id',
        tokenize='unicode61'
    );
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_text_segments_ai AFTER INSERT ON text_segments BEGIN
        INSERT INTO text_segments_fts(rowid, text) VALUES (new.id, new.text);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_text_segments_ad AFTER DELETE ON text_segments BEGIN
        INSERT INTO text_segments_fts(text_segments_fts, rowid, text)
            VALUES ('delete', old.id, old.text);
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_text_segments_au AFTER UPDATE ON text_segments BEGIN
        INSERT INTO text_segments_fts(text_segments_fts, rowid, text)
            VALUES ('delete', old.id, old.text);
        INSERT INTO text_segments_fts(rowid, text) VALUES (new.id, new.text);
    END;
    """,
)
