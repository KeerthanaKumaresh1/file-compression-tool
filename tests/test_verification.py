import os
import tempfile
import unittest

from compressor.errors import VerificationError
from compressor.file_format import write_bytes
from compressor.verification import (assert_lossless, files_identical, verify_lossless)
from tests.helpers import compress_bytes


class TestVerification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def test_matching_files(self):
        original, packed = self.path("a.txt"), self.path("a.hfc")
        write_bytes(original, b"some data some data")
        write_bytes(packed, compress_bytes(b"some data some data"))
        self.assertTrue(verify_lossless(original, packed))
        assert_lossless(original, packed)

    def test_different_original_fails(self):
        original, packed = self.path("a.txt"), self.path("a.hfc")
        write_bytes(original, b"changed after compression")
        write_bytes(packed, compress_bytes(b"some data some data"))
        self.assertFalse(verify_lossless(original, packed))
        with self.assertRaises(VerificationError):
            assert_lossless(original, packed)

    def test_files_identical(self):
        a, b, c = self.path("a"), self.path("b"), self.path("c")
        write_bytes(a, b"same")
        write_bytes(b, b"same")
        write_bytes(c, b"different")
        self.assertTrue(files_identical(a, b))
        self.assertFalse(files_identical(a, c))