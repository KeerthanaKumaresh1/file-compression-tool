"""BL15 - Corrupted File Detection."""
import zlib

from .errors import CorruptedFileError


def validate_structure(original_size, padding, freq):
    """Sanity-check the header values before decoding."""
    if padding > 7:
        raise CorruptedFileError("Header is damaged (invalid padding value).")
    if any(count <= 0 for count in freq.values()):
        raise CorruptedFileError("Frequency table is damaged (invalid count).")
    if sum(freq.values()) != original_size:
        raise CorruptedFileError("Header is damaged (table does not match the original size).")


def check_payload_length(freq, codes, padding, payload):
    """The number of encoded bits is known exactly from freq and codes."""
    expected_bits = sum(freq[s] * len(codes[s]) for s in freq)
    expected_bytes = (expected_bits + 7) // 8
    if len(payload) != expected_bytes:
        raise CorruptedFileError(
            f"Data section is {len(payload)} bytes but {expected_bytes} were expected "
            "(file is truncated or has extra data).")
    if padding != expected_bytes * 8 - expected_bits:
        raise CorruptedFileError("Padding information is inconsistent.")


def check_checksum(data, expected_crc):
    """Compare the CRC-32 of the decoded data with the one stored at compression time."""
    if zlib.crc32(data) != expected_crc:
        raise CorruptedFileError("Checksum mismatch - the file is corrupted.")