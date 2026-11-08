"""Tests for BL2 input file validation (SR-1, SR-5)."""

import os
import tempfile
import unittest

from compressor.errors import FileValidationError
from compressor.file_validation import read_file_bytes, validate_input_file
from compressor.utils import format_size


class TestValidateInputFile(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = self.temp.name
        self.path = os.path.join(self.folder, "data.txt")
        with open(self.path, "wb") as handle:
            handle.write(b"content")

    def test_valid_file_is_accepted(self):
        self.assertEqual(validate_input_file(self.path), self.path)

    def test_blank_path_is_rejected(self):
        for value in ("", "   ", None):
            with self.assertRaises(FileValidationError):
                validate_input_file(value)

    def test_missing_file_is_rejected(self):
        with self.assertRaises(FileValidationError) as ctx:
            validate_input_file(os.path.join(self.folder, "nope.txt"))
        self.assertIn("File not found", str(ctx.exception))

    def test_folder_is_rejected(self):
        with self.assertRaises(FileValidationError) as ctx:
            validate_input_file(self.folder)
        self.assertIn("folder", str(ctx.exception))

    def test_empty_file_is_rejected_by_default(self):
        empty = os.path.join(self.folder, "empty.txt")
        open(empty, "wb").close()
        with self.assertRaises(FileValidationError) as ctx:
            validate_input_file(empty)
        self.assertIn("empty", str(ctx.exception))

    def test_empty_file_allowed_when_requested(self):
        empty = os.path.join(self.folder, "empty.txt")
        open(empty, "wb").close()
        self.assertEqual(validate_input_file(empty, allow_empty=True), empty)

    def test_read_file_bytes(self):
        self.assertEqual(read_file_bytes(self.path), b"content")

    def test_read_failure_is_a_validation_error(self):
        with self.assertRaises(FileValidationError):
            read_file_bytes(self.folder)


class TestFormatSize(unittest.TestCase):

    def test_units(self):
        self.assertEqual(format_size(512), "512 B")
        self.assertEqual(format_size(2048), "2.00 KB")
        self.assertEqual(format_size(5 * 1024 * 1024), "5.00 MB")
        self.assertEqual(format_size(3 * 1024 ** 3), "3.00 GB")
        self.assertEqual(format_size(2048 * 1024 ** 3), "2048.00 GB")


if __name__ == "__main__":
    unittest.main()
