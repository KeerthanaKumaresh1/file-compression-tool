"""BL20 - End-to-end integration tests."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compressor import cli
from compressor.pipeline import compress_file, decompress


class TestEndToEnd(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

        self.source = self.root / "sample.txt"
        self.source.write_bytes(
            b"File compression integration testing. " * 100
        )

        self.history_file = self.root / "history.json"
        patcher = patch(
            "compressor.pipeline._history.history_file",
            self.history_file
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_compression_creates_output(self):
        result = compress_file(self.source)

        output = Path(result["output_path"])
        self.assertTrue(output.exists())
        self.assertGreater(output.stat().st_size, 0)

    def test_complete_compression_and_decompression(self):
        compressed = compress_file(self.source)

        restored_path = self.root / "restored.txt"
        restored = decompress(
            compressed["output_path"],
            restored_path
        )

        self.assertTrue(Path(restored["output_path"]).exists())
        self.assertEqual(
            Path(restored["output_path"]).read_bytes(),
            self.source.read_bytes()
        )

    def test_cli_parser(self):
        parser = cli.build_parser()

        args = parser.parse_args([
            "compress",
            str(self.source),
            "--verify"
        ])

        self.assertEqual(args.command, "compress")
        self.assertTrue(args.verify)

    def test_empty_history_command(self):
        with patch(
            "compressor.cli.CompressionHistory"
        ) as history_class:
            history_class.return_value.get_history.return_value = []

            result = cli.main(["history"])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
