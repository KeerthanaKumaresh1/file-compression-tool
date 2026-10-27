
"""BL8 - Compressed File Creation (file format + writer).

All numeric fields are stored in big-endian order.
"""
import os
import struct
import zlib

from .errors import FileCreationError


MAGIC = b"HFC1"
HEADER_FORMAT = ">4sQIBH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
ENTRY_FORMAT = ">BI"
ENTRY_SIZE = struct.calcsize(ENTRY_FORMAT)
EXTENSION = ".hfc"
MAX_FILE_SIZE = 0xFFFFFFFF


def encode_to_bytes(data, codes):
    """Encode source bytes and pack their Huffman bits into bytes.

    Returns (payload_bytes, padding_bits).
    """
    table = {
        symbol: (int(code, 2), len(code))
        for symbol, code in codes.items()
    }

    out = bytearray()
    buffer = 0
    nbits = 0

    for byte in data:
        value, length = table[byte]
        buffer = (buffer << length) | value
        nbits += length

        while nbits >= 8:
            nbits -= 8
            out.append((buffer >> nbits) & 0xFF)

        buffer &= (1 << nbits) - 1

    padding = 0
    if nbits:
        padding = 8 - nbits
        out.append((buffer << padding) & 0xFF)

    return bytes(out), padding


def build_compressed_bytes(data, freq, codes):
    """Return the complete compressed file as bytes."""
    if len(data) > MAX_FILE_SIZE:
        raise FileCreationError(
            "File is too large to compress (limit is 4 GB)."
        )

    payload, padding = encode_to_bytes(data, codes)

    header = struct.pack(
        HEADER_FORMAT,
        MAGIC,
        len(data),
        zlib.crc32(data),
        padding,
        len(freq),
    )

    table = b"".join(
        struct.pack(ENTRY_FORMAT, symbol, freq[symbol])
        for symbol in sorted(freq)
    )

    return header + table + payload


def write_bytes(path, data):
    """Write bytes to a file and clean up a partial output on failure."""
    try:
        handle = open(path, "wb")
    except OSError as error:
        raise FileCreationError(
            f"Could not create '{path}': {error.strerror or error}"
        ) from error

    try:
        with handle:
            handle.write(data)
    except OSError as error:
        try:
            os.remove(path)
        except OSError:
            pass

        raise FileCreationError(
            f"Could not write '{path}': {error.strerror or error}"
        ) from error

