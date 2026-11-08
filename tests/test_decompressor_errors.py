"""Tests for every error branch of the decompressor (SR-2, FR-9)."""

import struct
import unittest
import zlib

from compressor.decompressor import (
    decode_payload,
    decompress_bytes,
    decompress_file,
    parse_compressed,
)
from compressor.errors import CorruptedFileError, FileValidationError
from compressor.file_format import ENTRY_FORMAT, HEADER_FORMAT, MAGIC
from compressor.huffman_tree import build_huffman_tree
from tests.helpers import compress_bytes

import os
import tempfile


def make_file(original_size, padding, table, payload=b"", crc=0):
    header = struct.pack(
        HEADER_FORMAT, MAGIC, original_size, crc, padding, len(table)
    )
    body = b"".join(struct.pack(ENTRY_FORMAT, s, n) for s, n in table)
    return header + body + payload


class TestParseErrors(unittest.TestCase):

    def test_padding_above_seven(self):
        with self.assertRaises(CorruptedFileError):
            parse_compressed(make_file(1, 8, [(65, 1)]))

    def test_incomplete_frequency_table(self):
        raw = make_file(3, 0, [(65, 1), (66, 2)])[:-2]
        with self.assertRaises(CorruptedFileError):
            parse_compressed(raw)

    def test_duplicate_symbol(self):
        with self.assertRaises(CorruptedFileError):
            parse_compressed(make_file(2, 0, [(65, 1), (65, 1)]))

    def test_zero_frequency(self):
        with self.assertRaises(CorruptedFileError):
            parse_compressed(make_file(1, 0, [(65, 0), (66, 1)]))

    def test_valid_file_is_parsed(self):
        size, crc, pad, freq, payload = parse_compressed(
            make_file(3, 2, [(65, 1), (66, 2)], b"\x40", crc=9)
        )
        self.assertEqual((size, crc, pad, payload), (3, 9, 2, b"\x40"))
        self.assertEqual(freq, {65: 1, 66: 2})


class TestDecompressErrors(unittest.TestCase):

    def test_frequency_total_must_match_size(self):
        raw = make_file(5, 0, [(65, 1), (66, 2)], b"\x00")
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(raw)

    def test_empty_original_with_payload_is_rejected(self):
        with self.assertRaises(CorruptedFileError):
            decode_payload(b"\x01", None, 0, 0)

    def test_empty_original_is_empty_bytes(self):
        self.assertEqual(decode_payload(b"", None, 0, 0), b"")

    def test_empty_table_with_data_is_rejected(self):
        with self.assertRaises(CorruptedFileError):
            decode_payload(b"", None, 5, 0)

    def test_negative_bit_count_is_rejected(self):
        root = build_huffman_tree({65: 1, 66: 1})
        with self.assertRaises(CorruptedFileError):
            decode_payload(b"", root, 2, 5)

    def test_wrong_decoded_length_is_rejected(self):
        root = build_huffman_tree({65: 1, 66: 1})
        # 1 symbol decoded, but 2 were expected
        with self.assertRaises(CorruptedFileError):
            decode_payload(b"\x00", root, 2, 7)

    def test_partial_code_at_end_is_rejected(self):
        root = build_huffman_tree({65: 1, 66: 1, 67: 2})
        # 67 has the code "0"; 65 and 66 have two-bit codes starting "1".
        # A lone "1" bit ends in the middle of a code.
        with self.assertRaises(CorruptedFileError):
            decode_payload(b"\x80", root, 1, 7)

    def test_crc_mismatch_is_rejected(self):
        # bytes 4..11 hold the size (8 bytes); the CRC32 is at bytes 12..15
        good = bytearray(compress_bytes(b"checksum test data"))
        good[12:16] = struct.pack(">I", zlib.crc32(b"other"))
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(bytes(good))


class TestDecompressFile(unittest.TestCase):

    def test_missing_file_is_a_validation_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileValidationError):
                decompress_file(
                    os.path.join(folder, "none.hfc"),
                    os.path.join(folder, "out"),
                )

    def test_round_trip_through_files(self):
        data = b"file based round trip " * 20
        with tempfile.TemporaryDirectory() as folder:
            src = os.path.join(folder, "a.hfc")
            out = os.path.join(folder, "a.txt")
            with open(src, "wb") as handle:
                handle.write(compress_bytes(data))
            self.assertEqual(decompress_file(src, out), len(data))
            with open(out, "rb") as handle:
                self.assertEqual(handle.read(), data)


if __name__ == "__main__":
    unittest.main()
