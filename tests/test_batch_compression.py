"""Tests for BL18 batch compression."""

import tempfile
import unittest
from pathlib import Path

from compressor.batch_compression import compress_files


class TestBatchCompression(unittest.TestCase):
    def test_compresses_multiple_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "compressed"
            output.mkdir()

            first = root / "first.txt"
            second = root / "second.txt"
            first.write_bytes(b"hello hello hello")
            second.write_bytes(b"batch compression test")

            results = compress_files([first, second], output_dir=output)

            self.assertEqual(len(results), 2)
            for result in results:
                self.assertTrue(Path(result["output_path"]).is_file())

    def test_rejects_empty_input_list(self):
        with self.assertRaises(ValueError):
            compress_files([])


if __name__ == "__main__":
    unittest.main()
