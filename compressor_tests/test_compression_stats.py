
import unittest

from compressor.compression_stats import (
    calculate_statistics,
    format_statistics,
)


class TestCompressionStatistics(unittest.TestCase):

    def test_normal_compression(self):
        result = calculate_statistics(1000, 600, 4000)

        self.assertEqual(result["original_size"], 1000)
        self.assertEqual(result["compressed_size"], 600)
        self.assertEqual(result["space_saved"], 400)
        self.assertEqual(result["space_saved_percent"], 40.0)
        self.assertEqual(result["compression_ratio"], 1.67)
        self.assertEqual(result["average_bits_per_symbol"], 4.0)

    def test_compressed_file_larger_than_original(self):
        result = calculate_statistics(100, 120)

        self.assertEqual(result["space_saved"], -20)
        self.assertEqual(result["space_saved_percent"], -20.0)

    def test_empty_original_file(self):
        result = calculate_statistics(0, 0)

        self.assertEqual(result["space_saved"], 0)
        self.assertIsNone(result["compression_ratio"])
        self.assertIsNone(result["average_bits_per_symbol"])

    def test_zero_byte_compressed_file(self):
        result = calculate_statistics(100, 0)

        self.assertIsNone(result["compression_ratio"])

    def test_negative_size_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_statistics(-1, 10)

    def test_non_integer_size_is_rejected(self):
        with self.assertRaises(TypeError):
            calculate_statistics(10.5, 5)

    def test_negative_total_bits_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_statistics(100, 50, -1)

    def test_format_statistics(self):
        result = calculate_statistics(1000, 500, 4000)
        formatted = format_statistics(result)

        self.assertEqual(formatted["Original size"], "1000 bytes")
        self.assertEqual(formatted["Compressed size"], "500 bytes")
        self.assertEqual(formatted["Space saved percentage"], "50.00%")
        self.assertEqual(formatted["Compression ratio"], "2.0:1")


if __name__ == "__main__":
    unittest.main()
