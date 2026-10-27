
"""Tests for BL5 - Huffman Tree."""

import unittest

from compressor.frequency import calculate_frequencies
from compressor.huffman_tree import (
    HuffmanNode,
    build_huffman_tree,
    symbol_label,
)


class TestHuffmanTree(unittest.TestCase):
    def test_empty_table_gives_no_tree(self):
        self.assertIsNone(build_huffman_tree({}))

    def test_single_symbol_is_a_leaf(self):
        root = build_huffman_tree({97: 4})

        self.assertTrue(root.is_leaf())
        self.assertEqual(root.symbol, 97)
        self.assertEqual(root.freq, 4)

    def test_root_frequency_is_total(self):
        freq = calculate_frequencies(b"abracadabra")
        root = build_huffman_tree(freq)

        self.assertEqual(root.freq, 11)

    def test_same_tree_every_time(self):
        freq = calculate_frequencies(b"mississippi")

        first = build_huffman_tree(freq)
        second = build_huffman_tree(freq)

        self.assertEqual(first.left.freq, second.left.freq)
        self.assertEqual(first.right.freq, second.right.freq)

    def test_internal_node_has_children(self):
        root = build_huffman_tree({97: 2, 98: 3})

        self.assertFalse(root.is_leaf())
        self.assertEqual(root.freq, 5)
        self.assertIsNotNone(root.left)
        self.assertIsNotNone(root.right)

    def test_symbol_labels(self):
        self.assertEqual(symbol_label(9), "\\t")
        self.assertEqual(symbol_label(10), "\\n")
        self.assertEqual(symbol_label(13), "\\r")
        self.assertEqual(symbol_label(32), "space")
        self.assertEqual(symbol_label(65), "A")
        self.assertEqual(symbol_label(0), "0x00")
        self.assertEqual(symbol_label(255), "0xFF")

    def test_leaf_node(self):
        node = HuffmanNode(5, symbol=65)
        self.assertTrue(node.is_leaf())


if __name__ == "__main__":
    unittest.main()
