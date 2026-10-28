import unittest

from compressor.huffman_code_table import build_huffman_code_table


class TestHuffmanCodeTable(unittest.TestCase):

    def test_lists_every_distinct_byte(self):
        frequencies = {65: 3, 66: 2, 67: 1}
        codes = {65: "0", 66: "10", 67: "11"}

        table = build_huffman_code_table(frequencies, codes)

        self.assertEqual([row["byte"] for row in table], [65, 66, 67])

    def test_displays_correct_frequencies_and_codes(self):
        frequencies = {65: 3, 66: 2}
        codes = {65: "0", 66: "1"}

        table = build_huffman_code_table(frequencies, codes)

        self.assertEqual(table[0]["frequency"], 3)
        self.assertEqual(table[0]["code"], "0")
        self.assertEqual(table[1]["frequency"], 2)
        self.assertEqual(table[1]["code"], "1")

    def test_handles_non_printable_bytes(self):
        frequencies = {0: 2, 10: 1, 255: 3}
        codes = {0: "0", 10: "10", 255: "11"}

        table = build_huffman_code_table(frequencies, codes)

        self.assertEqual(len(table), 3)
        self.assertEqual(table[0]["display"], "b'\\x00'")
        self.assertEqual(table[1]["display"], "b'\\n'")
        self.assertEqual(table[2]["display"], "b'\\xff'")

    def test_rejects_mismatched_symbols(self):
        frequencies = {65: 3, 66: 2}
        codes = {65: "0"}

        with self.assertRaises(ValueError):
            build_huffman_code_table(frequencies, codes)

    def test_rejects_invalid_byte_values(self):
        frequencies = {256: 1}
        codes = {256: "0"}

        with self.assertRaises(ValueError):
            build_huffman_code_table(frequencies, codes)


if __name__ == "__main__":
    unittest.main()