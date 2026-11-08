"""Tests for the command line interface (BL20): every command and flag."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compressor import cli
from compressor.history import CompressionHistory


class TestCliCommands(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.history_file = self.root / "history.json"

        self.src = self.root / "sample.txt"
        self.src.write_bytes(b"AAAABBBCCD" * 50)

        for target in ("compressor.pipeline._history.history_file",):
            patcher = patch(target, self.history_file)
            patcher.start()
            self.addCleanup(patcher.stop)

        patcher = patch(
            "compressor.cli.CompressionHistory",
            lambda: CompressionHistory(self.history_file),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main([str(a) for a in argv])
        return code, out.getvalue(), err.getvalue()

    def test_compress_prints_statistics(self):
        code, out, _ = self.run_cli("compress", self.src)
        self.assertEqual(code, 0)
        self.assertIn("Original size: 500 bytes", out)
        self.assertIn("Compression ratio", out)
        self.assertTrue((self.root / "sample.txt.hfc").exists())

    def test_compress_table_tree_verify_time(self):
        code, out, _ = self.run_cli(
            "compress", self.src, "--table", "--tree", "--verify", "--time"
        )
        self.assertEqual(code, 0)
        self.assertIn("Huffman Code Table", out)
        self.assertIn("Huffman Tree", out)
        self.assertIn("Verification passed", out)
        self.assertIn("Time:", out)

    def test_decompress_with_time(self):
        self.run_cli("compress", self.src)
        out_path = self.root / "restored.txt"
        code, out, _ = self.run_cli(
            "decompress", self.root / "sample.txt.hfc", "-o", out_path, "--time"
        )
        self.assertEqual(code, 0)
        self.assertIn("Decompressed:", out)
        self.assertIn("Time:", out)
        self.assertEqual(out_path.read_bytes(), self.src.read_bytes())

    def test_verify_command_success_and_failure(self):
        self.run_cli("compress", self.src)
        hfc = self.root / "sample.txt.hfc"
        code, out, _ = self.run_cli("verify", self.src, hfc)
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

        other = self.root / "other.txt"
        other.write_bytes(b"different")
        code, _, err = self.run_cli("verify", other, hfc)
        self.assertEqual(code, 6)
        self.assertIn("Error", err)

    def test_history_lists_then_clears(self):
        self.run_cli("compress", self.src)
        code, out, _ = self.run_cli("history")
        self.assertEqual(code, 0)
        self.assertIn("compression", out)

        code, out, _ = self.run_cli("history", "--clear")
        self.assertIn("History cleared", out)
        _, out, _ = self.run_cli("history")
        self.assertIn("No history available", out)

    def test_missing_input_returns_exit_code_2(self):
        code, _, err = self.run_cli("compress", self.root / "nope.txt")
        self.assertEqual(code, 2)
        self.assertIn("Error", err)

    def test_existing_output_returns_exit_code_5(self):
        self.run_cli("compress", self.src)
        code, _, err = self.run_cli("compress", self.src)
        self.assertEqual(code, 5)
        code, _, _ = self.run_cli("compress", self.src, "--overwrite")
        self.assertEqual(code, 0)

    def test_corrupt_input_returns_exit_code_4(self):
        bad = self.root / "bad.hfc"
        bad.write_bytes(b"not a real compressed file")
        code, _, err = self.run_cli("decompress", bad)
        self.assertEqual(code, 4)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
