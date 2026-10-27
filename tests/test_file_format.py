import os
import tempfile
import unittest

from compressor.errors import FileCreationError
from compressor.file_format import (
    HEADER_SIZE,
    MAGIC,
    build_compressed_bytes,
    encode_to_bytes,
    write_bytes,
)


class TestFileFormat(unittest.TestCase):
    def test_encode_known_bits(self):
        codes = {0: "0", 1: "10", 2: "11"}
        self.assertEqual(
            encode_to_bytes(bytes([0, 1, 2, 0]), codes),
            (b"\x58", 2),
        )

    def test_encode_exact_multiple_of_eight(self):
        self.assertEqual(
            encode_to_bytes(bytes([0] * 8), {0: "1"}),
            (b"\xff", 0),
        )

    def test_header_and_table_layout(self):
        blob = build_compressed_bytes(
            bytes([0, 1]),
            {0: 1, 1: 1},
            {0: "0", 1: "1"},
        )
        self.assertTrue(blob.startswith(MAGIC))
        self.assertEqual(HEADER_SIZE, 19)
        self.assertEqual(len(blob), 19 + 2 * 5 + 1)

    def test_write_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.hfc")
            write_bytes(path, b"abc")

            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), b"abc")

    def test_write_failure_gives_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing_folder", "out.hfc")

            with self.assertRaises(FileCreationError):
                write_bytes(path, b"abc")


if __name__ == "__main__":
    unittest.main()
