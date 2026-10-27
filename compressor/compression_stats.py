
"""BL11 - Compression statistics for the File Compression Tool."""


def calculate_statistics(original_size, compressed_size, total_bits=None):
    """Calculate file compression statistics.

    Args:
        original_size: Original file size in bytes.
        compressed_size: Compressed file size in bytes.
        total_bits: Optional number of bits used to encode the symbols.

    Returns:
        A dictionary containing the calculated statistics.
    """
    if not isinstance(original_size, int) or isinstance(original_size, bool):
        raise TypeError("Original size must be an integer.")
    if not isinstance(compressed_size, int) or isinstance(compressed_size, bool):
        raise TypeError("Compressed size must be an integer.")
    if original_size < 0 or compressed_size < 0:
        raise ValueError("File sizes cannot be negative.")

    if total_bits is not None:
        if not isinstance(total_bits, int) or isinstance(total_bits, bool):
            raise TypeError("Total bits must be an integer.")
        if total_bits < 0:
            raise ValueError("Total bits cannot be negative.")

    if original_size == 0:
        space_saved = 0
        space_saved_percent = 0.0
        compression_ratio = None
    else:
        space_saved = original_size - compressed_size
        space_saved_percent = (space_saved / original_size) * 100
        compression_ratio = original_size / compressed_size if compressed_size else None

    average_bits_per_symbol = (
        total_bits / original_size
        if total_bits is not None and original_size > 0
        else None
    )

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "space_saved": space_saved,
        "space_saved_percent": round(space_saved_percent, 2),
        "compression_ratio": (
            round(compression_ratio, 2)
            if compression_ratio is not None
            else None
        ),
        "average_bits_per_symbol": (
            round(average_bits_per_symbol, 2)
            if average_bits_per_symbol is not None
            else None
        ),
    }


def format_statistics(statistics):
    """Format calculated statistics for display."""
    ratio = statistics["compression_ratio"]
    average = statistics["average_bits_per_symbol"]

    return {
        "Original size": f'{statistics["original_size"]} bytes',
        "Compressed size": f'{statistics["compressed_size"]} bytes',
        "Space saved": f'{statistics["space_saved"]} bytes',
        "Space saved percentage": f'{statistics["space_saved_percent"]:.2f}%',
        "Compression ratio": f"{ratio}:1" if ratio is not None else "N/A",
        "Average bits per symbol": (
            str(average) if average is not None else "N/A"
        ),
    }
