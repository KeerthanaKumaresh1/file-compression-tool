
"""BL5 - Huffman Tree."""

from .min_heap import MinHeap


class HuffmanNode:
    """A node of the Huffman tree.

    Leaf nodes hold a symbol. Internal nodes hold the combined frequency
    of their children and have no symbol.
    """

    def __init__(self, freq, symbol=None, left=None, right=None):
        self.freq = freq
        self.symbol = symbol
        self.left = left
        self.right = right

    def is_leaf(self):
        """Return True if this node has no children."""
        return self.left is None and self.right is None


def symbol_label(symbol):
    """Return a readable label for a byte value."""
    special = {
        9: "\\t",
        10: "\\n",
        13: "\\r",
        32: "space",
    }

    if symbol in special:
        return special[symbol]

    if 32 < symbol < 127:
        return chr(symbol)

    return f"0x{symbol:02X}"


def build_huffman_tree(freq):
    """Build a Huffman tree from a {symbol: count} frequency table.

    Returns the root node, or None when the frequency table is empty.
    """
    if not freq:
        return None

    heap = MinHeap()

    # Sorted insertion ensures deterministic tie-breaking.
    for symbol in sorted(freq):
        heap.push(freq[symbol], HuffmanNode(freq[symbol], symbol))

    # Repeatedly combine the two nodes with the lowest frequencies.
    while len(heap) > 1:
        f1, first = heap.pop()
        f2, second = heap.pop()

        parent = HuffmanNode(
            f1 + f2,
            symbol=None,
            left=first,
            right=second,
        )
        heap.push(f1 + f2, parent)

    return heap.pop()[1]
