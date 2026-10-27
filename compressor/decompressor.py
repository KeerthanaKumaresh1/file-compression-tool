"""BL9 - File Decompression."""
import struct

from .errors import CorruptedFileError
from .file_format import (ENTRY_FORMAT, ENTRY_SIZE, HEADER_FORMAT, HEADER_SIZE,
                          MAGIC, write_bytes)
from .file_validation import read_file_bytes
from .huffman_tree import build_huffman_tree


def parse_compressed(raw):
    """Split a compressed file into its parts.

    Returns (original_size, crc, padding, freq, payload).
    """
    if len(raw) < HEADER_SIZE:
        raise CorruptedFileError("File is too short to be a compressed file.")
    magic, original_size, crc, padding, count = struct.unpack_from(HEADER_FORMAT, raw, 0)
    if magic != MAGIC:
        raise CorruptedFileError("Not a valid compressed file (wrong signature).")
    table_end = HEADER_SIZE + count * ENTRY_SIZE
    if len(raw) < table_end:
        raise CorruptedFileError("The frequency table is incomplete.")
    freq = {}
    for i in range(count):
        symbol, number = struct.unpack_from(ENTRY_FORMAT, raw, HEADER_SIZE + i * ENTRY_SIZE)
        if symbol in freq:
            raise CorruptedFileError("The frequency table contains a duplicate symbol.")
        freq[symbol] = number
    return original_size, crc, padding, freq, raw[table_end:]


def decode_payload(payload, root, original_size, padding):
    """Walk the Huffman tree bit by bit and rebuild the original bytes."""
    if original_size == 0:
        return b""
    if root is None:
        raise CorruptedFileError("The frequency table is empty.")
    if root.is_leaf():                   # file made of one repeated byte
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
        raise CorruptedFileError("The data does not decode to the expected size.")
    return bytes(out)


def decompress_bytes(raw):
    original_size, crc, padding, freq, payload = parse_compressed(raw)
    root = build_huffman_tree(freq)
    return decode_payload(payload, root, original_size, padding)


def decompress_file(input_path, output_path):
    """Read a compressed file and write the restored original. Returns its size."""
    data = decompress_bytes(read_file_bytes(input_path))
    write_bytes(output_path, data)
    return len(data)