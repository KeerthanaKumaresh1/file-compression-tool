
"""BL12 - Huffman Tree Visualization."""


def _get(node, attribute, default=None):
    """Read an attribute from a node."""
    if isinstance(node, dict):
        return node.get(attribute, default)
    return getattr(node, attribute, default)


def _symbol_label(symbol):
    """Return a readable label for a byte or symbol."""
    if isinstance(symbol, int) and 0 <= symbol <= 255:
        if 32 <= symbol <= 126:
            char = chr(symbol)
            if char in ("'", "\\"):
                char = "\\" + char
            return char
        return f"0x{symbol:02X}"

    if isinstance(symbol, bytes):
        return repr(symbol)

    return str(symbol)


def _is_leaf(node):
    """A leaf has neither a left nor a right child."""
    return (
        _get(node, "left") is None
        and _get(node, "right") is None
    )


def _label(node):
    """Format a node's symbol and frequency."""
    frequency = _get(node, "freq", _get(node, "frequency", "?"))

    if _is_leaf(node):
        symbol = _get(node, "symbol", _get(node, "char", "?"))
        return f"'{_symbol_label(symbol)}' ({frequency})"

    return f"({frequency})"


def render_tree(root, max_depth=8):
    """Render a Huffman tree as an indented text diagram.

    Nodes should expose left, right, and freq/frequency attributes.
    Leaf nodes should expose symbol or char.
    """
    if root is None:
        return "(empty tree)"

    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")

    lines = [_label(root)]

    def walk(node, prefix, depth):
        if _is_leaf(node):
            return

        if depth >= max_depth:
            lines.append(prefix + "└── ...")
            return

        children = [
            ("0", _get(node, "left")),
            ("1", _get(node, "right")),
        ]

        children = [
            (bit, child)
            for bit, child in children
            if child is not None
        ]

        for index, (bit, child) in enumerate(children):
            last = index == len(children) - 1
            branch = "└──" if last else "├──"
            lines.append(f"{prefix}{branch} {bit}: {_label(child)}")

            next_prefix = prefix + ("    " if last else "│   ")
            walk(child, next_prefix, depth + 1)

    walk(root, "", 0)
    return "\n".join(lines)

