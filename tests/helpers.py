"""Shared helper functions for compression tests."""

from compressor.frequency import calculate_frequencies
from compressor.huffman_tree import build_huffman_tree
from compressor.huffman_codes import generate_huffman_codes
from compressor.file_format import build_compressed_bytes


def compress_bytes(data):
    """Compress bytes using the project's Huffman compression modules."""
    frequencies = calculate_frequencies(data)
    tree = build_huffman_tree(frequencies)
    codes = generate_huffman_codes(tree)
    return build_compressed_bytes(data, frequencies, codes)
