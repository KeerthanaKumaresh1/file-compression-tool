"""BL3 - Frequency Analysis."""


def calculate_frequencies(data):
    """Count how often each byte value (0-255) appears in `data`.

    Returns a dict {byte_value: count}, sorted by byte value.
    """
    freq = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1
    return dict(sorted(freq.items()))