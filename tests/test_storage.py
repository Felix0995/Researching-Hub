"""Tests for local file storage service, hashing, deduplication, and safety.

Covers Phase 1 required storage test scenarios:
- Accurate SHA-256 calculation
- Deduplication without creating redundant physical copies
- Byte-for-byte file content preservation
- Path traversal prevention
- Stream-based ingestion
- Integrity verification and corruption detection
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from researchhub.storage import (
    StorageFileNotFoundError,
    StorageIntegrityError,
    StoragePathTraversalError,
    StorageService,
)


def test_sha256_computation(tmp_path: Path) -> None:
    """Case 8: SHA-256 calculation matches hashlib on identical content."""
    service = StorageService(storage_dir=tmp_path / "storage")

    content = b"ResearchHub MBA V1.0 Sample Content for Hashing Test." * 100
    expected_hash = hashlib.sha256(content).hexdigest().lower()

    sample_file = tmp_path / "sample.pdf"
    sample_file.write_bytes(content)

    actual_hash, total_bytes = service.compute_hash(sample_file)
    assert actual_hash == expected_hash
    assert total_bytes == len(content)


def test_duplicate_file_detection(tmp_path: Path) -> None:
    """Case 9: Storing identical file bytes twice returns duplicate flag without new file."""
    storage_dir = tmp_path / "storage"
    service = StorageService(storage_dir=storage_dir)

    content = b"PDF Mock Content Byte Stream"
    file1 = tmp_path / "paper_v1.pdf"
    file1.write_bytes(content)

    file2 = tmp_path / "paper_copy.pdf"
    file2.write_bytes(content)

    res1 = service.store_file(file1)
    assert res1.is_duplicate is False

    res2 = service.store_file(file2)
    assert res2.is_duplicate is True
    assert res2.sha256 == res1.sha256
    assert res2.stored_relpath == res1.stored_relpath

    # Verify only one file physically exists in the sharded directory
    prefix = res1.sha256[:2]
    files_in_prefix = list((storage_dir / prefix).iterdir())
    assert len(files_in_prefix) == 1


def test_file_byte_preservation(tmp_path: Path) -> None:
    """Case 10: Stored file content is preserved byte-for-byte."""
    service = StorageService(storage_dir=tmp_path / "storage")

    # Generate binary content with mixed bytes
    binary_content = bytes(range(256)) * 50
    source_file = tmp_path / "document.docx"
    source_file.write_bytes(binary_content)

    res = service.store_file(source_file)
    assert res.size_bytes == len(binary_content)

    # Read back through stream chunks
    chunks = list(service.read_chunks(res.stored_relpath))
    retrieved_content = b"".join(chunks)

    assert retrieved_content == binary_content
    assert hashlib.sha256(retrieved_content).hexdigest() == res.sha256


def test_path_traversal_prevention(tmp_path: Path) -> None:
    """Case 11: Attempted path traversal outside storage directory raises error."""
    service = StorageService(storage_dir=tmp_path / "storage")

    malicious_paths = [
        "../secret.txt",
        "../../etc/passwd",
        "/etc/shadow",
        "subdir/../../outside.pdf",
        "",
        "   ",
    ]

    for bad_path in malicious_paths:
        with pytest.raises(StoragePathTraversalError):
            service.resolve_path(bad_path)


def test_store_stream_and_duplicate(tmp_path: Path) -> None:
    """Verify storing bytes from a file-like stream with deduplication."""
    service = StorageService(storage_dir=tmp_path / "storage")

    stream_data = b"Streamed PDF Document Data for MBA Research."
    res1 = service.store_stream(io.BytesIO(stream_data), "streamed_paper.pdf")

    assert res1.is_duplicate is False
    assert res1.file_type == "pdf"
    assert res1.mime_type == "application/pdf"

    # Store identical stream again
    res2 = service.store_stream(io.BytesIO(stream_data), "streamed_paper_again.pdf")
    assert res2.is_duplicate is True
    assert res2.sha256 == res1.sha256


def test_verify_file_integrity_and_corruption_detection(tmp_path: Path) -> None:
    """Verify integrity check succeeds on valid file and catches corruption."""
    service = StorageService(storage_dir=tmp_path / "storage")

    content = b"Original uncorrupted academic research text."
    source = tmp_path / "article.pdf"
    source.write_bytes(content)

    res = service.store_file(source)
    assert service.verify_file_integrity(res.stored_relpath, res.sha256) is True

    # Simulate bit rot / accidental corruption
    abs_path = service.resolve_path(res.stored_relpath)
    abs_path.write_bytes(b"Corrupted content bytes.")

    with pytest.raises(StorageIntegrityError):
        service.verify_file_integrity(res.stored_relpath, res.sha256)


def test_missing_file_handling(tmp_path: Path) -> None:
    """Verify attempting to store or read non-existent file raises appropriate error."""
    service = StorageService(storage_dir=tmp_path / "storage")

    with pytest.raises(StorageFileNotFoundError):
        service.store_file(tmp_path / "non_existent.pdf")

    with pytest.raises(StorageFileNotFoundError):
        list(service.read_chunks("aa/non_existent.pdf"))
