"""Extra edge-case tests added in Sprint 3 / testing week.

They cover error paths and defensive branches that the original tests did
not reach (identified from the branch-coverage report).
"""

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compressor import cli, file_format
from compressor.batch_compression import compress_files
from compressor.compression_stats import calculate_statistics
from compressor.error_handler import exit_code_for, run_safely
from compressor.errors import (
    CompressionError,
    FileCreationError,
    FileValidationError,
    OutputExistsError,
)
from compressor.file_validation import validate_input_file
from compressor.history import CompressionHistory
from compressor.huffman_code_table import build_huffman_code_table
from compressor.huffman_tree import HuffmanNode
from compressor.min_heap import MinHeap
from compressor.output_protection import write_output
from compressor.tree_visualizer import render_tree
from compressor.verification import file_hash


class TestMinHeapEdges(unittest.TestCase):

    def test_empty_heap_errors(self):
        heap = MinHeap()
        self.assertTrue(heap.is_empty())
        with self.assertRaises(IndexError):
            heap.pop()
        with self.assertRaises(IndexError):
            heap.peek()

    def test_peek_and_order(self):
        heap = MinHeap()
        for priority, name in ((5, "e"), (1, "a"), (3, "c"), (1, "b")):
            heap.push(priority, name)
        self.assertEqual(heap.peek(), (1, "a"))
        self.assertEqual([heap.pop()[1] for _ in range(4)], ["a", "b", "c", "e"])


class TestStatisticsEdges(unittest.TestCase):

    def test_non_integer_compressed_size(self):
        with self.assertRaises(TypeError):
            calculate_statistics(10, "5")

    def test_non_integer_total_bits(self):
        with self.assertRaises(TypeError):
            calculate_statistics(10, 5, total_bits=1.5)


class TestErrorHandlerEdges(unittest.TestCase):

    def test_base_compression_error_exit_code(self):
        self.assertEqual(exit_code_for(CompressionError("x")), 1)

    def test_keyboard_interrupt(self):
        def stop():
            raise KeyboardInterrupt
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(run_safely(stop), 130)
        self.assertIn("Cancelled", err.getvalue())

    def test_memory_error(self):
        def boom():
            raise MemoryError
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(run_safely(boom), 7)
        self.assertIn("not enough memory", err.getvalue())


class TestFileFormatEdges(unittest.TestCase):

    def test_size_limit_is_enforced(self):
        with patch.object(file_format, "MAX_FILE_SIZE", 4):
            with self.assertRaises(FileCreationError):
                file_format.build_compressed_bytes(b"abcde", {97: 5}, {97: "0"})

    def test_write_bytes_cannot_create(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileCreationError):
                file_format.write_bytes(os.path.join(folder, "no", "x.hfc"), b"1")

    def test_partial_file_removed_when_write_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.hfc")

            class Broken:
                def __enter__(self):
                    return self
                def __exit__(self, *exc):
                    return False
                def write(self, data):
                    raise OSError(28, "No space left on device")

            Path(path).write_bytes(b"partial output")
            with patch("builtins.open", return_value=Broken()):
                with self.assertRaises(FileCreationError):
                    file_format.write_bytes(path, b"data")
            self.assertFalse(os.path.exists(path))


class TestHistoryEdges(unittest.TestCase):

    def test_history_file_with_wrong_json_type(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "h.json"
            path.write_text('{"not": "a list"}', encoding="utf-8")
            self.assertEqual(CompressionHistory(path).get_history(), [])

    def test_non_serialisable_details_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            history = CompressionHistory(Path(folder) / "h.json")
            with self.assertRaises(ValueError):
                history.add_entry("compression", "a", "b", bad=object())


class TestCodeTableEdges(unittest.TestCase):

    def test_arguments_must_be_mappings(self):
        with self.assertRaises(TypeError):
            build_huffman_code_table([1], {1: "0"})

    def test_negative_frequency_rejected(self):
        with self.assertRaises(ValueError):
            build_huffman_code_table({65: -1}, {65: "0"})

    def test_code_must_be_a_string(self):
        with self.assertRaises(TypeError):
            build_huffman_code_table({65: 1}, {65: 0})


class TestOutputProtectionEdges(unittest.TestCase):

    def test_file_appearing_after_check_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "o.hfc")
            with patch(
                "compressor.output_protection.prepare_output_path",
                return_value=path,
            ):
                Path(path).write_bytes(b"first")
                with self.assertRaises(OutputExistsError):
                    write_output(path, b"second")
            self.assertEqual(Path(path).read_bytes(), b"first")

    def test_os_error_while_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "o.hfc")
            with patch("builtins.open", side_effect=OSError("disk full")):
                with self.assertRaises(FileCreationError):
                    write_output(path, b"x")


class TestTreeVisualizerEdges(unittest.TestCase):

    def test_dictionary_nodes_and_special_symbols(self):
        tree = {
            "freq": 6,
            "left": {"freq": 3, "symbol": 39},      # '
            "right": {
                "freq": 3,
                "left": {"freq": 1, "symbol": 10},  # newline -> 0x0A
                "right": {"freq": 2, "symbol": b"xy"},
            },
        }
        text = render_tree(tree)
        self.assertIn("\\'", text)
        self.assertIn("0x0A", text)
        self.assertIn("b'xy'", text)

    def test_non_byte_symbol(self):
        leaf = HuffmanNode(1, symbol="Q")
        self.assertIn("Q", render_tree(leaf))


class TestVerificationEdges(unittest.TestCase):

    def test_unreadable_file_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileValidationError):
                file_hash(folder)


class TestValidationEdges(unittest.TestCase):

    def test_unreadable_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "secret.txt")
            Path(path).write_bytes(b"x")
            with patch("os.access", return_value=False):
                with self.assertRaises(FileValidationError) as ctx:
                    validate_input_file(path)
            self.assertIn("permission", str(ctx.exception))


class TestBatchAndCliEdges(unittest.TestCase):

    def test_batch_default_output_next_to_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "a.txt"
            src.write_bytes(b"batch default folder")
            results = compress_files([src])
            self.assertEqual(results[0]["output_path"], str(src) + ".hfc")
            self.assertTrue((Path(folder) / "a.txt.hfc").exists())

    def test_decompress_command_without_time_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / "a.txt"
            src.write_bytes(b"decompress without timing " * 10)
            history = root / "history.json"
            with patch("compressor.pipeline._history.history_file", history):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    cli.main(["compress", str(src)])
                    code = cli.main(
                        ["decompress", str(src) + ".hfc", "-o", str(root / "b.txt")]
                    )
            self.assertEqual(code, 0)
            self.assertNotIn("Speed:", out.getvalue().split("Decompressed:")[1])


if __name__ == "__main__":
    unittest.main()
