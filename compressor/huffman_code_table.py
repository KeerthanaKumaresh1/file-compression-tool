"""BL13 - Build a frequency and Huffman code table for byte data."""


def build_huffman_code_table(frequencies, codes):
    """Return rows containing each byte, its frequency, and its Huffman code.

    Args:
        frequencies: Mapping of byte values to occurrence counts.
        codes: Mapping of byte values to Huffman bit strings.

    Returns:
        A list of dictionaries sorted by byte value.
    """
    if not hasattr(frequencies, "items") or not hasattr(codes, "items"):
        raise TypeError("frequencies and codes must be mappings")

    if set(frequencies) != set(codes):
        raise ValueError("frequencies and codes must contain the same symbols")

    rows = []

    for symbol in sorted(frequencies):
        if not isinstance(symbol, int) or not 0 <= symbol <= 255:
            raise ValueError("symbols must be byte values from 0 to 255")

        frequency = frequencies[symbol]
        code = codes[symbol]

        if not isinstance(frequency, int) or isinstance(frequency, bool) or frequency < 0:
            raise ValueError("frequencies must be non-negative integers")

        if not isinstance(code, str):
            raise TypeError("Huffman codes must be strings")

        rows.append({
            "byte": symbol,
            "display": repr(bytes([symbol])),
            "frequency": frequency,
            "code": code,
        })

    return rows