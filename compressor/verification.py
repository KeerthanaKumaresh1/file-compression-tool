"""BL10 - Lossless Verification."""
import hashlib

from .decompressor import decompress_bytes
from .errors import FileValidationError, VerificationError
from .file_validation import read_file_bytes


def file_hash(path):
    """SHA-256 of a file, read in chunks so big files do not fill the memory."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except OSError as error:
        raise FileValidationError(f"Could not read '{path}': {error.strerror or error}") from error
    return digest.hexdigest()


def files_identical(path_a, path_b):
    return file_hash(path_a) == file_hash(path_b)


def verify_lossless(original_path, compressed_path):
    """True if decompressing `compressed_path` gives back `original_path` exactly."""
    restored = decompress_bytes(read_file_bytes(compressed_path))
    return hashlib.sha256(restored).hexdigest() == file_hash(original_path)


def assert_lossless(original_path, compressed_path):
    if not verify_lossless(original_path, compressed_path):
        raise VerificationError("Verification FAILED: the restored data differs from the original.")