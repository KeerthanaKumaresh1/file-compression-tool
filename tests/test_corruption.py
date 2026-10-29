import unittest

from compressor.decompressor import decompress_bytes
from compressor.errors import CorruptedFileError
from tests.helpers import compress_bytes

DATA = b"the quick brown fox jumps over the lazy dog " * 3


class TestCorruption(unittest.TestCase):
    def setUp(self):
        self.blob = compress_bytes(DATA)

    def test_good_file_passes(self):
        self.assertEqual(decompress_bytes(self.blob), DATA)

    def test_too_short(self):
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(b"HFC1")

    def test_wrong_signature(self):
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(b"XXXX" + self.blob[4:])

    def test_not_a_compressed_file(self):
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(b"just some ordinary text, not compressed at all")

    def test_truncated(self):
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(self.blob[:-3])

    def test_extra_bytes(self):
        with self.assertRaises(CorruptedFileError):
            decompress_bytes(self.blob + b"\x00")

    def test_every_single_byte_change_is_detected(self):
        for i in range(len(self.blob)):
            bad = bytearray(self.blob)
            bad[i] ^= 0xFF
            with self.assertRaises(CorruptedFileError, msg=f"byte {i} not detected"):
                decompress_bytes(bytes(bad))