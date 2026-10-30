"""BL20 - Integration: complete compression and decompression workflows."""

from .compression_stats import calculate_statistics
from .decompressor import decompress_file
from .file_format import build_compressed_bytes
from .file_validation import validate_input_file, read_file_bytes
from .frequency import calculate_frequencies
from .history import CompressionHistory
from .huffman_codes import generate_huffman_codes
from .huffman_tree import build_huffman_tree
from .output_protection import (
    default_compressed_name,
    default_decompressed_name,
    prepare_output_path,
    write_output,
)


_history = CompressionHistory()


def compress_file(input_path, output_path=None, overwrite=False):
    """Compress one file and return its result and metadata."""

    validate_input_file(input_path)

    if output_path is None:
        output_path = default_compressed_name(input_path)

    output_path = prepare_output_path(
        output_path,
        overwrite=overwrite
    )

    data = read_file_bytes(input_path)
    frequencies = calculate_frequencies(data)
    tree = build_huffman_tree(frequencies)
    codes = generate_huffman_codes(tree)

    compressed_data = build_compressed_bytes(
        data,
        frequencies,
        codes
    )

    write_output(
        output_path,
        compressed_data,
        overwrite=overwrite
    )

    total_bits = sum(
        frequencies[symbol] * len(codes[symbol])
        for symbol in frequencies
    )

    stats = calculate_statistics(
        len(data),
        len(compressed_data),
        total_bits
    )

    _history.add_entry(
        "compression",
        input_path,
        output_path,
        original_size=len(data),
        compressed_size=len(compressed_data)
    )

    return {
        "output_path": str(output_path),
        "stats": stats,
        "frequencies": frequencies,
        "codes": codes,
        "tree": tree,
    }


def decompress(input_path, output_path=None, overwrite=False):
    """Decompress one file and record the operation."""

    validate_input_file(input_path)

    if output_path is None:
        output_path = default_decompressed_name(input_path)

    output_path = prepare_output_path(
        output_path,
        overwrite=overwrite
    )

    restored_size = decompress_file(input_path, output_path)

    _history.add_entry(
        "decompression",
        input_path,
        output_path,
        restored_size=restored_size
    )

    return {
        "output_path": str(output_path),
        "restored_size": restored_size,
    }
