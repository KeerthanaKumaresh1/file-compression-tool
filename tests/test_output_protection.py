
"""Tests for BL14 - Output & Overwrite Protection."""

import tempfile
import unittest
from pathlib import Path

from compressor.errors import FileCreationError, OutputExistsError
from compressor.output_protection import (
    default_compressed_name,
    default_decompressed_name,
    prepare_output_path,
    write_output,
)


class TestOutputProtection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_compressed_name(self):
        self.assertEqual(
            default_compressed_name("notes.txt"),
            "notes.txt.hfc",
        )

    def test_default_decompressed_name(self):
        self.assertEqual(
            default_decompressed_name("notes.txt.hfc"),
            "notes_restored.txt",
        )

    def test_default_decompressed_name_without_hfc_extension(self):
        self.assertEqual(
            default_decompressed_name("notes.txt"),
            "notes_restored.txt",
        )

    def test_prepare_new_output_path(self):
        output = self.directory / "new.hfc"

        self.assertEqual(
            prepare_output_path(output),
            str(output),
        )

    def test_existing_output_is_protected(self):
        output = self.directory / "existing.hfc"
        output.write_bytes(b"original")

        with self.assertRaises(OutputExistsError):
            prepare_output_path(output)

        self.assertEqual(output.read_bytes(), b"original")

    def test_overwrite_can_be_explicitly_allowed(self):
        output = self.directory / "existing.hfc"
        output.write_bytes(b"original")

        self.assertEqual(
            prepare_output_path(output, overwrite=True),
            str(output),
        )

    def test_write_output_creates_file(self):
        output = self.directory / "new.hfc"

        result = write_output(output, b"compressed data")

        self.assertEqual(result, str(output))
        self.assertEqual(output.read_bytes(), b"compressed data")

    def test_write_output_does_not_overwrite_by_default(self):
        output = self.directory / "existing.hfc"
        output.write_bytes(b"keep me")

        with self.assertRaises(OutputExistsError):
            write_output(output, b"replace me")

        self.assertEqual(output.read_bytes(), b"keep me")

    def test_write_output_overwrites_when_requested(self):
        output = self.directory / "existing.hfc"
        output.write_bytes(b"old")

        write_output(output, b"new", overwrite=True)

        self.assertEqual(output.read_bytes(), b"new")

    def test_missing_directory_is_rejected(self):
        output = self.directory / "missing" / "new.hfc"

        with self.assertRaises(FileCreationError):
            prepare_output_path(output)

    def test_directory_cannot_be_used_as_output(self):
        with self.assertRaises(FileCreationError):
            prepare_output_path(self.directory)

    def test_non_boolean_overwrite_is_rejected(self):
        with self.assertRaises(TypeError):
            prepare_output_path(self.directory / "new.hfc", overwrite="yes")


if __name__ == "__main__":
    unittest.main()
