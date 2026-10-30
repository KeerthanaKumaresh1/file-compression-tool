"""BL20 - Command line interface for the File Compression Tool."""

import argparse

from .compression_stats import format_statistics
from .error_handler import run_safely
from .errors import VerificationError
from .history import CompressionHistory
from .huffman_code_table import build_huffman_code_table
from .performance import format_performance, measure
from .pipeline import compress_file, decompress
from .tree_visualizer import render_tree
from .utils import format_size
from .verification import assert_lossless, verify_lossless


def build_parser():
    parser = argparse.ArgumentParser(
        prog="file-compression-tool",
        description="Huffman file compression tool"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    comp = sub.add_parser("compress", help="Compress a file")
    comp.add_argument("input")
    comp.add_argument("-o", "--output")
    comp.add_argument("--overwrite", action="store_true")
    comp.add_argument("--table", action="store_true")
    comp.add_argument("--tree", action="store_true")
    comp.add_argument("--verify", action="store_true")
    comp.add_argument("--time", action="store_true")

    dec = sub.add_parser("decompress", help="Decompress a file")
    dec.add_argument("input")
    dec.add_argument("-o", "--output")
    dec.add_argument("--overwrite", action="store_true")
    dec.add_argument("--time", action="store_true")

    ver = sub.add_parser("verify", help="Verify lossless compression")
    ver.add_argument("original")
    ver.add_argument("compressed")

    hist = sub.add_parser("history", help="Show operation history")
    hist.add_argument("--clear", action="store_true")

    return parser


def _compress(args):
    result, report = measure(
        compress_file,
        args.input,
        args.output,
        args.overwrite,
        track_memory=args.time
    )

    print(f"Compressed: {args.input} -> {result['output_path']}")

    for label, value in format_statistics(result["stats"]).items():
        print(f"{label}: {value}")

    if args.table:
        rows = build_huffman_code_table(
            result["frequencies"],
            result["codes"]
        )
        print("\nHuffman Code Table")
        for row in rows:
            print(row)

    if args.tree:
        print("\nHuffman Tree")
        print(render_tree(result["tree"]))

    if args.verify:
        assert_lossless(args.input, result["output_path"])
        print("Verification passed: the file restores exactly.")

    if args.time:
        print(format_performance(report, result["stats"]["original_size"]))


def _decompress(args):
    result, report = measure(
        decompress,
        args.input,
        args.output,
        args.overwrite,
        track_memory=args.time
    )

    print(
        f"Decompressed: {args.input} -> {result['output_path']} "
        f"({format_size(result['restored_size'])})"
    )

    if args.time:
        print(format_performance(report, result["restored_size"]))


def _verify(args):
    if not verify_lossless(args.original, args.compressed):
        raise VerificationError(
            "The restored data differs from the original file."
        )

    print("OK: The compressed file restores the original exactly.")


def _history(args):
    history = CompressionHistory()

    if args.clear:
        history.clear_history()
        print("History cleared.")
        return

    entries = history.get_history()

    if not entries:
        print("No history available.")
        return

    for entry in entries:
        print(
            f"{entry['timestamp']} | {entry['operation']} | "
            f"{entry['input_file']} -> {entry['output_file']}"
        )


def main(argv=None):
    args = build_parser().parse_args(argv)

    handlers = {
        "compress": _compress,
        "decompress": _decompress,
        "verify": _verify,
        "history": _history,
    }

    return run_safely(handlers[args.command], args)
