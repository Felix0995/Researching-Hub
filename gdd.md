# ResearchHub MBA V1.0 — Goals & Design Document (GDD)

- Version: 0.1-draft (implementation baseline)
- Date: 2026-11-22
- Status: DRAFT for approval of Git/agent governance; product architecture decisions below were already confirmed by Product Owner
- Product Owner: Individual MacBook user
- Delivery mode: Incremental, phase-gated development using Antigravity + GitHub PR review
- Note: This is a SOFTWARE Goals & Design Document, not a game design document.

## 1. Product vision and boundaries

Build a reliable **local-first personal academic knowledge library** that helps one person import, preserve, classify, search, read, excerpt, annotate, and export research material. The UI is in **Vietnamese** and source material is in **Vietnamese, English, and Traditional Chinese**. Although MBA is the initial use case, the system must support any subject area and independent projects.

### Confirmed architecture baseline

| Attribute | Decision |
|---|---|
| Users | Single user |
| Runtime | Local MacBook, browser access via localhost |
| Internet/API | No Internet required for normal use after setup; no OpenAI API |
| AI | Excluded from V1.0 |
| Expected library | 500–5,000 documents |
| Formats V1.0 | PDF, DOCX |
| Storage policy | Copy originals into application-managed local storage |
| Organization | Subject/domain AND project, many-to-many |
| Primary UI language | Vietnamese |
| Source/search languages | Vietnamese, English, Traditional Chinese |
| Stack | Python, Streamlit, SQLite, SQLite FTS5, PyMuPDF, python-docx, openpyxl |
| Export | Word DOCX and Excel XLSX |

### Success criteria

1. The user can import and manage a representative local library without losing original files.
2. Search reliably identifies relevant documents and source passages, with PDF page references when extractable.
3. Classifications, notes, excerpts, and projects survive application restarts.
4. The user can build manual literature-review summaries and export them to usable Word/Excel files.
5. Library data can be backed up and restored safely.
6. The source code is maintainable, tested, and auditable through GitHub phase PRs.

### Explicit non-goals for V1.0

- Chatbot, AI analysis, semantic vector retrieval, auto translation, LLM API, automated literature review.
- OCR of scanned PDFs; scanned content without an embedded text layer is tagged for future OCR.
- Cloud sync, remote access, multi-user accounts, hosted deployment, online collaboration, login/registration.
- Automatic web crawling, journal downloading, DOI enrichment requiring network services.
- Excel/PPTX input parsing (can be considered in V1.1); source formats for ingestion remain PDF/DOCX.

## 2. Roles and primary user journeys

**User role:** library owner. No separate admin/member roles or sign-in screen V1.0.

### J1 — Import and classify

1. Open import page, select one or multiple PDF/DOCX files.
2. Validate type, compute checksum, detect duplicate bytes; do not overwrite existing copy.
3. Copy valid file into managed storage and create document record.
4. Extract searchable text, capture page/segment position, record status/error.
5. User edits document title, language, type, year, author(s), domain(s), project(s), tag(s).
6. Document appears in library and eligible search results.

### J2 — Find and cite a source passage

1. Search metadata or content by typed keyword/phrase in any supported language.
2. Filter by year, document type, domain, project, language, tags, read status.
3. Inspect a contextual excerpt; open the document detail and PDF page when feasible.
4. Copy or save an exact excerpt linked to document and page/segment.
5. Add a personal note; never present a note as the document author's assertion.

### J3 — Prepare a literature review

1. Open a research project or create one.
2. Tag relevant documents to the project.
3. Complete structured, **manually entered** research-summary fields or notes (purpose, theory, method, variables, findings, limitations).
4. Select multiple documents to produce a tabular literature-review matrix.
5. Export to `.xlsx` or `.docx`, including source identification.

### J4 — Preserve and restore

1. Create a backup of database AND managed files, with manifest and integrity checks.
2. Restore into a non-destructive staging directory; verify contents before swap or guided manual cutover.
3. The operator can recover from an interrupted import or partial error without loss of originals.

## 3. Information architecture and nine screens

| ID | Screen | Responsibilities |
|---|---|---|
| S01 | Dashboard | Count documents, domains, projects, recent files, indexed/unindexed status, storage use |
| S02 | Import | Batch upload, format validation, deduplication, extraction progress and errors |
| S03 | Library | Paginated list, filters, sort, card/table view, select documents |
| S04 | Document Detail | File preview/download, edit metadata, authors, domains/projects/tags, notes/excerpts |
| S05 | Advanced Search | Metadata + full-text queries, snippets, sources, filters, no-text indicators |
| S06 | Domains & Projects | Manage subject hierarchy and research projects; link documents without copying |
| S07 | Research Notebook | Notes, verbatim source excerpts, manual academic analysis fields |
| S08 | Literature Matrix | Manual summary comparison, chosen columns, DOCX/XLSX export |
| S09 | Settings & Backups | Storage location, local preferences, index rebuild, backup, restore and integrity status |

Navigation: Dashboard / Library / Import / Search / Domains & Projects / Notebook / Literature Matrix / Settings. Detail appears from library/search. Layout: simple Vietnamese UI, consistent navigation, accessible text contrast, responsive but desktop-first.

### Proposed domain groups (editable, not hard-coded)

Business Administration (MBA), Finance, Marketing, Human Resource Management, Corporate Governance, Strategy, Service Management, Economics, Law, Language Learning, General Knowledge. The owner can add or edit subjects and nested child subjects.

## 4. Technology and system architecture

```
MacBook browser (localhost)
        |
Streamlit UI / navigation (Python)
        |
Services: documents | taxonomy | search | notes | matrix | backup
        |
Repositories / storage / extraction adapters
        |                             |
SQLite relational DB + FTS5     Managed original files
        |
Indexed text_segments + document metadata
```

Principles:
- Default local bind to `127.0.0.1`; do not expose to public interfaces.
- Domain and service logic must be independent of UI code to allow tests.
- Use transactions for metadata changes and robust staging/rollback for imported files.
- Do not parse uploaded content as executable instructions.
- SQLite is source of truth for metadata/relationships; original binary files are preserved on disk.
- Use `PRAGMA foreign_keys=ON`, integrity constraints, indexes, and a schema version/migration mechanism.
- Use project-root-relative configuration via app config and user-specific storage root; do not rely on fixed Mac user home name.
- Ensure UTF-8/Unicode throughout.

### Suggested repository layout (to refine in Phase 0)

```
researchhub-mba/
  AGENTS.md
  agent.md
  gdd.md
  README.md
  .gitignore
  pyproject.toml
  app.py
  researchhub/
    ui/
    services/
    repositories/
    parsers/
    storage/
    db/
    models/
    config.py
  scripts/
  tests/
  data/                # gitignored: SQLite, imported originals, extracted text, backups
  .github/workflows/   # CI, when Phase 0 establishes repo
```

Do not create `app_build/` just because an Antigravity tutorial uses it; keep app code in a normal reviewed Python package unless an approved tooling constraint requires otherwise.

## 5. Database design — 14 logical tables + full-text index

Primary keys may use SQLite integer IDs consistently; record timestamps in a consistent format. Final DDL is a Phase 1 deliverable and may refine non-breaking fields, but must maintain the entities/relationships below.

| Table | Key data / constraints | Relationships |
|---|---|---|
| `file_objects` | id, sha256 UNIQUE, stored_relpath UNIQUE, original_filename, MIME/type, size_bytes, created_at | one stored binary per distinct checksum |
| `documents` | id, file_object_id UNIQUE FK, title, document_type, language, year, DOI, abstract, read_status, extraction_status, created_at, updated_at | one document profile per managed original in V1.0 |
| `authors` | id, full_name, optional normalized_name | author library |
| `document_authors` | document_id, author_id, author_order; composite uniqueness | N:N |
| `domains` | id, name, optional parent_id FK, description | nested domains |
| `document_domains` | document_id, domain_id; composite PK | N:N |
| `projects` | id, name, description, status, timestamps | project library |
| `document_projects` | document_id, project_id; composite PK | N:N |
| `tags` | id, name UNIQUE or normalized equivalent | tag library |
| `document_tags` | document_id, tag_id; composite PK | N:N |
| `text_segments` | id, document_id, segment_order, source_kind, page_number nullable, paragraph_number nullable, text, extraction metadata | 1:N source text |
| `notes` | id, document_id, optional project_id, kind, body, structured manual research fields, timestamps | personal annotations |
| `excerpts` | id, document_id, text_segment_id nullable, page_number/paragraph reference, exact_quote, comment, timestamps | verbatim source quotes |
| `glossary_terms` | id, term_vi, term_en, term_zh_trad, aliases/tags, notes | manually curated multilingual glossary |

Virtual search index: `text_segments_fts`, mapped/synchronized to `text_segments` and rebuilt safely when needed. Consider indexing metadata separately or through targeted SQL queries; do not require a second primary datastore.

### Data integrity invariants

- `file_objects.sha256` unique; imports of byte-identical files must not create redundant originals.
- Relative paths only in persisted storage references; never construct unsafe paths from user filenames.
- Every text segment belongs to exactly one document.
- A PDF segment carries a real page reference; a DOCX segment uses paragraph/segment position rather than fabricated pagination.
- Domain, project, tag, author relations are N:N; deleting a relation does NOT delete the original file.
- Deletion of a source document is a separate, confirmed operation with safe file lifecycle; do not silently cascade-delete originals.
- Database and FTS index stay in sync via triggers or explicit reliable index updates, with index rebuild tool.
- Handle files with no extractable text as a distinct status, not as a successful empty index.

## 6. Search behavior (without AI)

1. Search document metadata: exact/partial title, author, year, DOI, tag, domain/project, notes where specified.
2. Full-text search uses SQLite FTS5 with Unicode-safe tokenizer and tested phrase queries.
3. Traditional Chinese 1–2 character strings require a targeted substring fallback if the selected FTS tokenizer cannot support them; do not incorrectly claim no matches.
4. Search results return document title, matched excerpt/snippet, document language, and reliable source location; PDF references use actual page indexes converted to human-facing 1-based page numbers.
5. Filter and sort without loading all 5,000 documents into the Streamlit UI at once.
6. Query UI explains where no indexed text exists (image-only scans, encrypted PDFs, extraction errors).
7. Trigram and Unicode tokenization should be benchmarked on Vietnamese/English/Traditional Chinese fixtures; refine based on tests, not assumptions.
8. No semantic or cross-language meaning search without user-curated glossary mappings; glossary expansions are manual and transparent.

## 7. File handling and document lifecycle

Proposed statuses: `pending`, `processing`, `indexed`, `no_extractable_text`, `failed`, `unsupported`.

Import pipeline: select → validate → checksum → duplicate check → staged copy → metadata insert → extraction → segment insert and indexing → final status. Failed extraction must never erase the safely imported original. Tests must cover interruptions and malformed files.

Use PyMuPDF for text-layer PDF extraction and page references. Use python-docx for DOCX paragraphs and headings. Limit memory use through per-document processing and controlled batch sizes; capture detailed error messages and allow retry. Preserve source files byte-for-byte.

## 8. Notes and research matrix

Recommended manual academic note fields:

- Research question / purpose
- Theory / conceptual framework
- Hypotheses
- Sample / country / time range
- Method (OLS, FEM, REM, SEM, etc.)
- Independent variables / dependent variables / controls
- Findings, limitations, relationship to user's own project

These are **owner-entered data**, not machine-generated evidence. Matrix allows user-selected docs, columns, search/filter, and export to `.xlsx` and `.docx`. Distinguish source quotations from personal synthesis.

## 9. Backup, privacy, and operational policies

- Backup encompasses SQLite in a consistent state plus managed binaries, a manifest/checksums, and schema version.
- Restore is non-destructive by default; verify in staging; require deliberate confirmation before replacing existing live library.
- Data folder and `.env` are gitignored. Source PDFs, DOCX and research notes should never be automatically uploaded to GitHub.
- No analytics beacons, external API calls, remote access, or user login requirement in V1.0.
- Application should provide a Vietnamese getting-started guide and simple Mac start/stop instructions.

## 10. Delivery phase plan (no implementation prompt authorized yet)

### Phase 0 — Repository and environment audit
**Scope:** inspect existing MacBook ResearchHub project (if available), preserve backup, confirm Python/Streamlit compatibility, confirm GitHub repository and visibility, create project root and governance docs, basic CI/test tooling.
**Exit gate:** owner approves the target repo (prefer a dedicated PRIVATE repo), runnable minimal app, working venv, `pytest` and lint available, no user data tracked by Git.

### Phase 1 — Foundation: storage and SQLite schema
**Scope:** project package structure, config, 14-table schema, migration/version tracking, repository interfaces, file storage service, integrity checks, test fixtures.
**Exit gate:** migrations reproducible; FK constraints enforced; path validation and file hashes tested; DB persists across restart.

### Phase 2 — Import, parsing, and document detail
**Scope:** PDF/DOCX uploads, batch import, checksum dedup, extraction statuses, text segments, metadata editing, document detail, safe original-file preview/download.
**Exit gate:** imports valid/invalid/duplicate fixtures correctly; PDF page numbers and DOCX paragraph locations checked; original files unchanged.

### Phase 3 — Classification and library organization
**Scope:** domains hierarchy, projects, tags, authors, many-to-many links, library list/filter/sort, read states.
**Exit gate:** one original can belong to multiple domains/projects; relationship deletion does not delete binary; filters work at representative scale.

### Phase 4 — Search and verified retrieval
**Scope:** FTS5 indexing/rebuild, metadata + full-text search, snippets/page markers, filters, short Chinese substring fallback, no-text notice.
**Exit gate:** Vietnamese, English, Chinese test queries return expected fixtures and locations; no fabricated page references; index consistency checked.

### Phase 5 — Notebook and excerpts
**Scope:** create/edit/delete notes, verbatim quotes and source location, manual structured research fields, list and search annotations.
**Exit gate:** quotations retain source linkage; notes are separate from source text; changes survive restart.

### Phase 6 — Literature matrix and exports
**Scope:** compare project papers, choose columns, manually entered research-summary fields, `.xlsx` and `.docx` exports, correct Unicode handling.
**Exit gate:** exported outputs open successfully, include selected rows/columns and reliable source identifiers.

### Phase 7 — Dashboard, backup, performance, release
**Scope:** dashboard counts/status, storage use, consistent backup/restore and staged recovery, indexing/repair controls, pagination/performance profiling, docs, user acceptance tests.
**Exit gate:** 12 acceptance scenarios passed and documented; backup restore validated; app stable with representative dataset; final owner acceptance.

### Dependency chain

`P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7`

Some UI increments may be developed alongside their services within the same phase, but phase completion remains sequential and must pass review.

## 11. Quality gates and 12 acceptance scenarios

1. Import a valid PDF, preserve original SHA-256 and reopen after restart.
2. Import a valid DOCX, retain searchable paragraphs and readable metadata.
3. Batch import with one malformed file; other imports complete and errors show clearly.
4. Upload identical file twice; no duplicate binary copy and no silent overwrite.
5. Assign one document to multiple domains and projects; remove link without deleting original.
6. Search a Vietnamese keyword/phrase with expected snippet.
7. Search English terms and find the correct page/segment.
8. Search Traditional Chinese including short 1–2-character query.
9. Search in scanned/no-text PDF; display honest no-text status, not OCR success.
10. Save notes and exact quotes; restart; verify source linkage and retained text.
11. Export a literature matrix to XLSX and DOCX with correct Vietnamese/Traditional Chinese characters.
12. Backup entire library and restore into a separate staging location; verify all sample data and file checksums.

Required nonfunctional evidence: tests/lint pass, no secrets/data in Git, storage paths portable within Mac project settings, schema migration safe, representative 500–5,000 record pagination/search baseline and report.

## 12. GitHub integration and review protocol

- **Repository selection remains pending approval.** The currently visible GitHub account/repository must not be assumed to be the target ResearchHub repo unless the owner confirms it.
- Dedicated PRIVATE repository `researchhub-mba` is recommended; creating it is a separate approved step.
- One branch per phase (`phase/00-foundation`, `phase/01-database`, etc.); use a PR, not direct writes to `main`.
- Antigravity pushes only the code, test fixtures that are safe to publish, and approved documentation. Never upload private documents or production DB.
- Each PR carries: scope, changed modules, design deltas, tests/CI, manual evidence, known limitations, and exact SHA.
- PM independently inspects changed code and CI status through GitHub connector when notified; comments identify exact defects/severity and ask for changes.
- No merge occurs without PM review recommendation and Product Owner approval.
- Remote code review cannot independently prove that the app works on the owner's Mac; local runtime acceptance and test evidence remain mandatory.

## 13. Open decisions and risks before Phase 0

- Confirm final GitHub target repo and PRIVATE visibility; do not assume an existing unrelated/public repo.
- Audit existing local `ResearchHub` files and salvage usable code instead of deleting them.
- Confirm Mac Python version and chip/RAM only as needed for compatibility/performance.
- Select a reasonable default storage root and local backup destination; configure rather than hard-code.
- Validate Chinese full-text fallback, PDF multi-column extraction order, and DOCX paragraph references against representative test documents.
- Select a maintainable schema migration mechanism and precise version pins at Phase 1.

## 14. Freeze / approval state

The **functional and architectural baseline above reflects already confirmed user choices**. The detailed Antigravity/Git review process and the repository target must be approved before Agent receives any coding-phase task. Until then, this GDD is a planning and governance artifact only.
