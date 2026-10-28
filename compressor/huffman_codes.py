
"""BL6 - Generate Huffman codes from a Huffman tree."""


def generate_huffman_codes(root):
    """Return a mapping of byte symbols to their Huffman bit strings.

    The left edge represents 0 and the right edge represents 1.
    Returns an empty dictionary for an empty tree.
    A tree containing only one symbol assigns that symbol the code "0".
    """
    codes = {}

    if root is None:
        return codes

    def traverse(node, prefix):
        if node.is_leaf():
            codes[node.symbol] = prefix or "0"
            return

        if node.left is not None:
            traverse(node.left, prefix + "0")

        if node.right is not None:
            traverse(node.right, prefix + "1")

    traverse(root, "")
    return codes
