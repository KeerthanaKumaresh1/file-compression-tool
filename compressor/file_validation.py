"""BL2 - File Validation."""
import os

from .errors import FileValidationError


def validate_input_file(path, allow_empty=False):
    """Check that `path` is a readable, non-empty file. Returns the path."""
    if not path or not str(path).strip():
        raise FileValidationError("No file path was given.")
    if not os.path.exists(path):
        raise FileValidationError(f"File not found: '{path}'")
    if os.path.isdir(path):
        raise FileValidationError(f"'{path}' is a folder, not a file.")
    if not os.access(path, os.R_OK):
        raise FileValidationError(f"No permission to read '{path}'.")
    if os.path.getsize(path) == 0 and not allow_empty:
        raise FileValidationError(f"'{path}' is empty - there is nothing to compress.")
    return path


def read_file_bytes(path):
    """Read a whole file as bytes (works for text and binary files)."""
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as error:
        raise FileValidationError(f"Could not read '{path}': {error.strerror or error}") from error