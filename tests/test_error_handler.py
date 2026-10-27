
import io
import unittest
from contextlib import redirect_stderr

from compressor.error_handler import exit_code_for, run_safely
from compressor.errors import (
    CompressionError,
    CorruptedFileError,
    FileValidationError,
)


class TestErrorHandler(unittest.TestCase):
    def test_known_error_codes(self):
        self.assertEqual(exit_code_for(FileValidationError("x")), 2)
        self.assertEqual(exit_code_for(CorruptedFileError("x")), 4)

    def test_unknown_compression_error(self):
        self.assertEqual(exit_code_for(CompressionError("x")), 1)

    def test_success(self):
        self.assertEqual(run_safely(lambda: None), 0)

    def test_known_error_message(self):
        def fail():
            raise FileValidationError("File not found")

        output = io.StringIO()
        with redirect_stderr(output):
            code = run_safely(fail)

        self.assertEqual(code, 2)
        self.assertIn("File not found", output.getvalue())

    def test_unexpected_error(self):
        def fail():
            raise RuntimeError("unexpected")

        output = io.StringIO()
        with redirect_stderr(output):
            code = run_safely(fail)

        self.assertEqual(code, 1)
        self.assertIn("Unexpected error", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()

