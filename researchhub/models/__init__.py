"""Data models and entity definitions for ResearchHub MBA V1.0.

Provides typed, dataclass representations of the core domain entities
defined in the GDD (Goals & Design Document).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FileObject:
    """Represents a managed physical binary file on disk."""

    id: Optional[int]
    sha256: str
    stored_relpath: str
    original_filename: str
    file_type: str  # 'pdf' or 'docx'
    mime_type: str
    size_bytes: int
    created_at: str


@dataclass(frozen=True)
class Document:
    """Represents an academic research document profile."""

    id: Optional[int]
    file_object_id: int
    title: str
    document_type: str = "other"  # journal_article, thesis, book, report, etc.
    language: str = "vi"  # vi, en, zh-Hant, other
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    read_status: str = "unread"  # unread, reading, read
    # extraction_status: pending, processing, indexed, no_extractable_text, failed, unsupported
    extraction_status: str = "pending"
    extraction_error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass(frozen=True)
class Author:
    """Represents a document author."""

    id: Optional[int]
    full_name: str
    normalized_name: Optional[str] = None
    created_at: Optional[str] = None


@dataclass(frozen=True)
class Domain:
    """Represents a subject / domain in the hierarchical taxonomy."""

    id: Optional[int]
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[str] = None


@dataclass(frozen=True)
class Project:
    """Represents a research project."""

    id: Optional[int]
    name: str
    description: Optional[str] = None
    status: str = "active"  # active, completed, archived, paused
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass(frozen=True)
class Tag:
    """Represents a keyword or user tag."""

    id: Optional[int]
    name: str
    created_at: Optional[str] = None


@dataclass(frozen=True)
class TextSegment:
    """Represents an extracted text segment from a document."""

    id: Optional[int]
    document_id: int
    segment_order: int
    source_kind: str = "body"  # title, abstract, heading, body, table, footnote
    page_number: Optional[int] = None  # 1-based page index for PDF
    paragraph_number: Optional[int] = None  # paragraph index for DOCX
    text: str = ""
    extraction_metadata: Optional[str] = None
    created_at: Optional[str] = None


@dataclass(frozen=True)
class Note:
    """Represents a personal research note or structured academic analysis."""

    id: Optional[int]
    document_id: int
    project_id: Optional[int]
    kind: str  # general, methodology, summary, critique, idea
    title: str
    body: str
    # Structured manual academic fields (Section 8 GDD)
    research_question: Optional[str] = None
    theory_framework: Optional[str] = None
    hypotheses: Optional[str] = None
    sample_context: Optional[str] = None
    method: Optional[str] = None
    variables: Optional[str] = None
    findings: Optional[str] = None
    limitations: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass(frozen=True)
class Excerpt:
    """Represents a verbatim excerpt linked to source location."""

    id: Optional[int]
    document_id: int
    text_segment_id: Optional[int] = None
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    exact_quote: str = ""
    comment: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass(frozen=True)
class GlossaryTerm:
    """Represents a multilingual glossary term (Vietnamese, English, Traditional Chinese)."""

    id: Optional[int]
    term_vi: str
    term_en: str
    term_zh_trad: Optional[str] = None
    aliases: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
