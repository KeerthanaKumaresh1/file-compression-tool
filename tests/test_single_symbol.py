"""Regression tests: files that contain only ONE distinct byte value.

Defect found during system validation (SYS-04, SYS-05): the compressor
wrote one payload bit per byte for a single-symbol file, but the
decompressor rejected any payload for such a file, so e.g. b"Z" or
b"A" * 5000 could be compressed but never restored.
"""

import unittest

from compressor.decompressor import decompress_bytes
from compressor.errors import CorruptedFileError
from tests.helpers import compress_bytes


class TestSingleSymbolFiles(unittest.TestCase):

    def test_one_byte_file_round_trips(self):
        self.assertEqual(decompress_bytes(compress_bytes(b"Z")), b"Z")

    def test_repeated_byte_round_trips(self):
        data = b"A" * 5000
        self.assertEqual(decompress_bytes(compress_bytes(data)), data)

    def test_byte_boundaries_round_trip(self):
        for size in (1, 7, 8, 9, 15, 16, 17):
            data = b"\x00" * size
            self.assertEqual(decompress_bytes(compress_bytes(data)), data, size)

    def test_payload_with_a_one_bit_is_rejected(self):
        blob = bytearray(compress_bytes(b"A" * 8))
        blob[-1] = 0x80
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(bytes(blob))

    def test_extra_payload_byte_is_rejected(self):
        blob = compress_bytes(b"A" * 8) + b"\x00"
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(blob)


if __name__ == "__main__":
    unittest.main()
