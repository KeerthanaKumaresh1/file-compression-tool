

"""BL9 - File Decompression."""
import struct
import zlib

from .errors import CorruptedFileError
from .file_format import (
    ENTRY_FORMAT,
    ENTRY_SIZE,
    HEADER_FORMAT,
    HEADER_SIZE,
    MAGIC,
    write_bytes,
)
from .file_validation import read_file_bytes
from .huffman_tree import build_huffman_tree


def parse_compressed(raw):
    """Split a compressed file into its parts.

    Returns (original_size, crc, padding, freq, payload).
    """
    if len(raw) < HEADER_SIZE:
        raise CorruptedFileError(
            "File is too short to be a compressed file."
        )

    magic, original_size, crc, padding, count = struct.unpack_from(
        HEADER_FORMAT, raw, 0
    )

    if magic != MAGIC:
        raise CorruptedFileError(
            "Not a valid compressed file (wrong signature)."
        )

    if padding > 7:
        raise CorruptedFileError("Padding information is invalid.")

    table_end = HEADER_SIZE + count * ENTRY_SIZE

    if len(raw) < table_end:
        raise CorruptedFileError("The frequency table is incomplete.")

    freq = {}

    for i in range(count):
        symbol, number = struct.unpack_from(
            ENTRY_FORMAT, raw, HEADER_SIZE + i * ENTRY_SIZE
        )

        if symbol in freq:
            raise CorruptedFileError(
                "The frequency table contains a duplicate symbol."
            )

        if number == 0:
            raise CorruptedFileError(
                "The frequency table contains an invalid frequency."
            )

        freq[symbol] = number

    payload = raw[table_end:]

    return original_size, crc, padding, freq, payload


def decode_payload(payload, root, original_size, padding):
    """Walk the Huffman tree bit by bit and rebuild the original bytes."""
    if original_size == 0:
        if payload or padding:
            raise CorruptedFileError(
                "Invalid compressed data for an empty file."
            )
        return b""

    if root is None:
        raise CorruptedFileError("The frequency table is empty.")

    if root.is_leaf():
        if payload or padding:
            raise CorruptedFileError(
                "Unexpected payload for a single-symbol file."
            )
        return bytes([root.symbol]) * original_size

    total_bits = len(payload) * 8 - padding

    if total_bits < 0:
        raise CorruptedFileError("Padding information is invalid.")

    out = bytearray()
    node = root

    for i in range(total_bits):
        bit = (payload[i >> 3] >> (7 - (i & 7))) & 1
        node = node.right if bit else node.left

        if node.is_leaf():
            out.append(node.symbol)
            node = root

    if node is not root or len(out) != original_size:
        raise CorruptedFileError(
            "The data does not decode to the expected size."
        )

    return bytes(out)


def decompress_bytes(raw):
    """Decompress data and verify its CRC32 checksum."""
    original_size, crc, padding, freq, payload = parse_compressed(raw)

    if sum(freq.values()) != original_size:
        raise CorruptedFileError(
            "Frequency table does not match the original file size."
        )

    root = build_huffman_tree(freq)

    restored = decode_payload(
        payload, root, original_size, padding
    )

    if zlib.crc32(restored) != crc:
        raise CorruptedFileError(
            "Corrupted file: CRC32 checksum mismatch."
        )

    return restored


def decompress_file(input_path, output_path):
    """Read a compressed file and write the restored original."""
    data = decompress_bytes(read_file_bytes(input_path))
    write_bytes(output_path, data)
    return len(data)




    
