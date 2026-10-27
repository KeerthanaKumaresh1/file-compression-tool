
import unittest
from dataclasses import dataclass

from compressor.tree_visualizer import render_tree


@dataclass
class Node:
    freq: int
    symbol: object = None
    left: object = None
    right: object = None


class TestTreeVisualizer(unittest.TestCase):
    def test_empty_tree(self):
        self.assertEqual(render_tree(None), "(empty tree)")

    def test_single_leaf(self):
        root = Node(freq=3, symbol=ord("a"))
        self.assertEqual(render_tree(root), "'a' (3)")

    def test_internal_nodes_and_branches(self):
        root = Node(
            freq=5,
            left=Node(freq=3, symbol=ord("a")),
            right=Node(freq=2, symbol=ord("b")),
        )

        result = render_tree(root)

        self.assertIn("(5)", result)
        self.assertIn("0: 'a' (3)", result)
        self.assertIn("1: 'b' (2)", result)

    def test_depth_limit(self):
        root = Node(
            freq=6,
            left=Node(
                freq=3,
                left=Node(freq=1, symbol=ord("a")),
                right=Node(freq=2, symbol=ord("b")),
            ),
            right=Node(freq=3, symbol=ord("c")),
        )

        self.assertIn("...", render_tree(root, max_depth=1))

    def test_negative_depth_rejected(self):
        with self.assertRaises(ValueError):
            render_tree(Node(freq=1, symbol=ord("a")), max_depth=-1)


if __name__ == "__main__":
    unittest.main()

