import os
import hashlib
from typing import Tuple, Optional
from backend.app.core.config import settings


class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_file(file_path: str, original_filename: str) -> Tuple[bool, str, int, str]:
    """
    Validates file existence, format, size, and corruption.
    Returns (is_valid, file_format, file_size, file_hash).
    """
    if not os.path.exists(file_path):
        raise FileValidationError(f"File not found on disk: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise FileValidationError(f"File '{original_filename}' is empty (0 bytes).")

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise FileValidationError(
            f"File '{original_filename}' size ({file_size / (1024*1024):.2f} MB) "
            f"exceeds limit of {settings.MAX_FILE_SIZE_MB} MB."
        )

    # Determine extension
    parts = original_filename.rsplit(".", 1)
    if len(parts) < 2:
        raise FileValidationError(f"File '{original_filename}' has no extension.")

    file_format = parts[1].lower()
    if file_format not in settings.ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"File format '.{file_format}' is not supported. "
            f"Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Check magic bytes / headers where applicable
    with open(file_path, "rb") as f:
        header = f.read(16)

    if file_format == "pdf" and not header.startswith(b"%PDF"):
        raise FileValidationError(f"Corrupted or invalid PDF header for '{original_filename}'.")

    file_hash = compute_file_hash(file_path)
    return True, file_format, file_size, file_hash

