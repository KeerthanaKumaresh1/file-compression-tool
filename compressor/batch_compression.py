"""BL18 - Batch Compression."""

from pathlib import Path

from .file_validation import validate_input_file, read_file_bytes
from .frequency import calculate_frequencies
from .huffman_tree import build_huffman_tree
from .huffman_codes import generate_huffman_codes
from .file_format import build_compressed_bytes
from .output_protection import default_compressed_name, write_output


def compress_files(input_paths, output_dir=None, overwrite=False):
    """Compress multiple files and return information about each result."""
    paths = list(input_paths)
    if not paths:
        raise ValueError("Select at least one file to compress.")

    results = []

    for input_path in paths:
        validate_input_file(input_path)
        data = read_file_bytes(input_path)
        frequencies = calculate_frequencies(data)
        tree = build_huffman_tree(frequencies)
        codes = generate_huffman_codes(tree)
        compressed = build_compressed_bytes(data, frequencies, codes)

        if output_dir is None:
            output_path = default_compressed_name(input_path)
        else:
            output_path = (
                Path(output_dir)
                / Path(default_compressed_name(input_path)).name
            )

        write_output(output_path, compressed, overwrite=overwrite)

        results.append({
            "input_path": str(input_path),
            "output_path": str(output_path),
            "original_size": len(data),
            "compressed_size": len(compressed),
        })

    return results
