"""Managed local file storage service for ResearchHub MBA V1.0.

Provides collision-resistant storage, SHA-256 chunked hashing,
duplicate detection, path traversal protection, and byte-for-byte file preservation.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Generator, Optional, Union

from researchhub.config import config

CHUNK_SIZE = 65536  # 64 KB chunk size for memory-efficient I/O


class StorageError(Exception):
    """Base exception for storage operations."""


class StoragePathTraversalError(StorageError):
    """Raised when an attempted path traversal outside storage root is detected."""


class StorageFileNotFoundError(StorageError):
    """Raised when a requested stored file is not found on disk."""


class StorageIntegrityError(StorageError):
    """Raised when file content does not match its expected checksum."""


@dataclass(frozen=True)
class StoreResult:
    """Outcome of a file store operation."""

    sha256: str
    stored_relpath: str
    original_filename: str
    file_type: str
    mime_type: str
    size_bytes: int
    is_duplicate: bool


def detect_file_type(filename: str) -> str:
    """Detect file type ('pdf', 'docx', 'other') from filename extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in (".docx", ".doc"):
        return "docx"
    return "other"


def detect_mime_type(filename: str) -> str:
    """Determine MIME type from filename extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if ext == ".doc":
        return "application/msword"
    return "application/octet-stream"


class StorageService:
    """Manages application-controlled file storage with integrity checking."""

    def __init__(self, storage_dir: Optional[Union[Path, str]] = None) -> None:
        """Initialize storage service with a target root directory."""
        if storage_dir is None:
            self._storage_dir = config.storage_dir.resolve()
        else:
            self._storage_dir = Path(storage_dir).resolve()

        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._staging_dir = self._storage_dir / ".staging"
        self._staging_dir.mkdir(parents=True, exist_ok=True)

    @property
    def storage_dir(self) -> Path:
        """Return the resolved storage root path."""
        return self._storage_dir

    def resolve_path(self, stored_relpath: str) -> Path:
        """Resolve a relative storage path safely, preventing directory traversal.

        Raises StoragePathTraversalError if resolved path escapes storage root or is absolute.
        """
        raw = stored_relpath.strip()
        if not raw:
            raise StoragePathTraversalError("Empty stored relative path is invalid.")

        # Disallow absolute paths
        if raw.startswith("/") or Path(raw).is_absolute():
            raise StoragePathTraversalError(
                f"Absolute path not permitted in storage relative path: '{stored_relpath}'."
            )

        target = (self._storage_dir / raw).resolve()

        # Strict containment check
        try:
            target.relative_to(self._storage_dir)
        except ValueError as err:
            raise StoragePathTraversalError(
                f"Path traversal detected: '{stored_relpath}' escapes storage root."
            ) from err

        if target == self._storage_dir:
            raise StoragePathTraversalError("Target path cannot be storage root itself.")

        return target

    def compute_hash(self, file_path: Union[Path, str]) -> tuple[str, int]:
        """Compute SHA-256 and size of a file in chunks to avoid high RAM usage."""
        p = Path(file_path)
        hasher = hashlib.sha256()
        total_bytes = 0

        with open(p, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
                total_bytes += len(chunk)

        return hasher.hexdigest().lower(), total_bytes

    def has_file(self, sha256: str) -> bool:
        """Check whether a file with the given SHA-256 checksum exists in storage."""
        sha = sha256.lower().strip()
        prefix = sha[:2]
        candidate_dir = self._storage_dir / prefix
        if not candidate_dir.is_dir():
            return False

        # Look for any file starting with this sha256
        for f in candidate_dir.iterdir():
            if f.is_file() and f.name.startswith(sha):
                return True
        return False

    def get_existing_relpath(self, sha256: str) -> Optional[str]:
        """Return existing relative path for a checksum, or None if not found."""
        sha = sha256.lower().strip()
        prefix = sha[:2]
        candidate_dir = self._storage_dir / prefix
        if not candidate_dir.is_dir():
            return None

        for f in candidate_dir.iterdir():
            if f.is_file() and f.name.startswith(sha):
                return f"{prefix}/{f.name}"
        return None

    def store_file(
        self,
        source_path: Union[Path, str],
        original_filename: Optional[str] = None,
    ) -> StoreResult:
        """Store a file into managed storage from a local filesystem path.

        Preserves original byte-for-byte; does not duplicate if SHA-256 exists.
        """
        src = Path(source_path)
        if not src.is_file():
            raise StorageFileNotFoundError(f"Source file not found: {source_path}")

        orig_name = original_filename or src.name
        sha256, size_bytes = self.compute_hash(src)

        file_type = detect_file_type(orig_name)
        mime_type = detect_mime_type(orig_name)
        ext = src.suffix.lower()

        # Check for duplicate
        existing_relpath = self.get_existing_relpath(sha256)
        if existing_relpath is not None:
            # Re-verify existing file integrity
            self.verify_file_integrity(existing_relpath, sha256)
            return StoreResult(
                sha256=sha256,
                stored_relpath=existing_relpath,
                original_filename=orig_name,
                file_type=file_type,
                mime_type=mime_type,
                size_bytes=size_bytes,
                is_duplicate=True,
            )

        # Generate collision-resistant relative path: {sha[:2]}/{sha}{ext}
        prefix = sha256[:2]
        filename_on_disk = f"{sha256}{ext}"
        stored_relpath = f"{prefix}/{filename_on_disk}"
        dest_dir = self._storage_dir / prefix
        dest_dir.mkdir(parents=True, exist_ok=True)
        final_dest = dest_dir / filename_on_disk

        # Staged atomic copy
        staging_filename = f".tmp_{uuid.uuid4().hex}"
        staging_path = self._staging_dir / staging_filename

        try:
            shutil.copyfile(src, staging_path)

            # Verify staged file checksum
            staged_hash, staged_size = self.compute_hash(staging_path)
            if staged_hash != sha256 or staged_size != size_bytes:
                raise StorageIntegrityError("Checksum verification failed during staged copy.")

            # Atomic replace into final destination
            os.replace(staging_path, final_dest)
        except Exception:
            if staging_path.exists():
                staging_path.unlink(missing_ok=True)
            raise

        return StoreResult(
            sha256=sha256,
            stored_relpath=stored_relpath,
            original_filename=orig_name,
            file_type=file_type,
            mime_type=mime_type,
            size_bytes=size_bytes,
            is_duplicate=False,
        )

    def store_stream(
        self,
        stream: BinaryIO,
        original_filename: str,
    ) -> StoreResult:
        """Store bytes from a stream into managed storage.

        Streams directly to a staging file while hashing on-the-fly.
        """
        orig_name = original_filename
        file_type = detect_file_type(orig_name)
        mime_type = detect_mime_type(orig_name)
        ext = Path(orig_name).suffix.lower()

        staging_filename = f".tmp_{uuid.uuid4().hex}"
        staging_path = self._staging_dir / staging_filename

        hasher = hashlib.sha256()
        size_bytes = 0

        try:
            with open(staging_path, "wb") as out_f:
                while chunk := stream.read(CHUNK_SIZE):
                    hasher.update(chunk)
                    size_bytes += len(chunk)
                    out_f.write(chunk)

            sha256 = hasher.hexdigest().lower()

            # Duplicate check
            existing_relpath = self.get_existing_relpath(sha256)
            if existing_relpath is not None:
                staging_path.unlink(missing_ok=True)
                self.verify_file_integrity(existing_relpath, sha256)
                return StoreResult(
                    sha256=sha256,
                    stored_relpath=existing_relpath,
                    original_filename=orig_name,
                    file_type=file_type,
                    mime_type=mime_type,
                    size_bytes=size_bytes,
                    is_duplicate=True,
                )

            # Move to destination
            prefix = sha256[:2]
            dest_dir = self._storage_dir / prefix
            dest_dir.mkdir(parents=True, exist_ok=True)
            final_dest = dest_dir / f"{sha256}{ext}"
            stored_relpath = f"{prefix}/{sha256}{ext}"

            os.replace(staging_path, final_dest)

            return StoreResult(
                sha256=sha256,
                stored_relpath=stored_relpath,
                original_filename=orig_name,
                file_type=file_type,
                mime_type=mime_type,
                size_bytes=size_bytes,
                is_duplicate=False,
            )
        except Exception:
            if staging_path.exists():
                staging_path.unlink(missing_ok=True)
            raise

    def verify_file_integrity(self, stored_relpath: str, expected_sha256: str) -> bool:
        """Verify that a stored file matches its expected SHA-256 checksum."""
        abs_path = self.resolve_path(stored_relpath)
        if not abs_path.is_file():
            raise StorageFileNotFoundError(f"Stored file does not exist: {stored_relpath}")

        actual_sha, _ = self.compute_hash(abs_path)
        if actual_sha != expected_sha256.lower():
            raise StorageIntegrityError(
                f"File integrity mismatch for {stored_relpath}: "
                f"expected {expected_sha256}, got {actual_sha}"
            )
        return True

    def read_chunks(
        self,
        stored_relpath: str,
        chunk_size: int = CHUNK_SIZE,
    ) -> Generator[bytes, None, None]:
        """Stream stored file contents in chunks."""
        abs_path = self.resolve_path(stored_relpath)
        if not abs_path.is_file():
            raise StorageFileNotFoundError(f"Stored file does not exist: {stored_relpath}")

        with open(abs_path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk
