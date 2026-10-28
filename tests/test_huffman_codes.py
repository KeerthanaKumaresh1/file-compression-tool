
import unittest

from compressor.huffman_tree import build_huffman_tree
from compressor.huffman_codes import generate_huffman_codes


class TestHuffmanCodes(unittest.TestCase):
    def test_empty_tree(self):
        self.assertEqual(generate_huffman_codes(None), {})

    def test_single_symbol(self):
        root = build_huffman_tree({65: 5})
        self.assertEqual(generate_huffman_codes(root), {65: "0"})

    def test_generates_code_for_every_symbol(self):
        frequencies = {ord("a"): 5, ord("b"): 2, ord("c"): 1}
        root = build_huffman_tree(frequencies)
        codes = generate_huffman_codes(root)

        self.assertEqual(set(codes), set(frequencies))
        self.assertTrue(all(set(code) <= {"0", "1"} for code in codes.values()))

    def test_prefix_free_codes(self):
        root = build_huffman_tree({65: 5, 66: 3, 67: 2, 68: 1})
        codes = generate_huffman_codes(root)

        for symbol, code in codes.items():
            for other_symbol, other_code in codes.items():
                if symbol != other_symbol:
                    self.assertFalse(other_code.startswith(code))

    def test_more_frequent_symbol_has_no_longer_code_in_example(self):
        root = build_huffman_tree({ord("a"): 8, ord("b"): 2, ord("c"): 1})
        codes = generate_huffman_codes(root)

        self.assertLess(len(codes[ord("a")]), len(codes[ord("c")]))


if __name__ == "__main__":
    unittest.main()
