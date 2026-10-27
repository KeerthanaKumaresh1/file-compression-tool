
"""Tests for BL19 - Compression History."""

import json
import tempfile
import unittest
from pathlib import Path

from compressor.history import CompressionHistory


class TestCompressionHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = Path(self.temp_dir.name) / "history.json"
        self.history = CompressionHistory(self.history_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_history_returns_empty_list(self):
        self.assertEqual(self.history.get_history(), [])

    def test_add_compression_entry(self):
        entry = self.history.add_entry(
            "compression", "input.txt", "output.huff",
            original_size=100, compressed_size=60
        )

        self.assertEqual(entry["operation"], "compression")
        self.assertEqual(entry["input_file"], "input.txt")
        self.assertEqual(entry["output_file"], "output.huff")
        self.assertIn("timestamp", entry)
        self.assertEqual(len(self.history.get_history()), 1)

    def test_add_decompression_entry(self):
        self.history.add_entry(
            "decompression", "output.huff", "restored.txt"
        )

        entries = self.history.get_history()
        self.assertEqual(entries[0]["operation"], "decompression")

    def test_history_is_saved_as_json(self):
        self.history.add_entry("compression", "a.txt", "a.huff")

        with self.history_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["input_file"], "a.txt")

    def test_invalid_operation_is_rejected(self):
        with self.assertRaises(ValueError):
            self.history.add_entry("copy", "a.txt", "b.txt")

    def test_history_is_limited_to_max_entries(self):
        history = CompressionHistory(self.history_file, max_entries=2)

        history.add_entry("compression", "first.txt", "first.huff")
        history.add_entry("compression", "second.txt", "second.huff")
        history.add_entry("compression", "third.txt", "third.huff")

        entries = history.get_history()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["input_file"], "second.txt")
        self.assertEqual(entries[1]["input_file"], "third.txt")

    def test_clear_history(self):
        self.history.add_entry("compression", "a.txt", "a.huff")
        self.history.clear_history()

        self.assertEqual(self.history.get_history(), [])

    def test_corrupted_json_returns_empty_list(self):
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text("{invalid json", encoding="utf-8")

        self.assertEqual(self.history.get_history(), [])

    def test_invalid_max_entries_is_rejected(self):
        with self.assertRaises(ValueError):
            CompressionHistory(self.history_file, max_entries=0)

        with self.assertRaises(TypeError):
            CompressionHistory(self.history_file, max_entries=1.5)


if __name__ == "__main__":
    unittest.main()
