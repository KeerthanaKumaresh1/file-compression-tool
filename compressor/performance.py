"""BL16 - Performance Measurement."""
import time
import tracemalloc
from dataclasses import dataclass

from .utils import format_size


@dataclass
class PerformanceReport:
    seconds: float
    peak_memory: int = 0


def measure(func, *args, track_memory=False, **kwargs):
    """Run a function and return (result, PerformanceReport)."""
    if track_memory:
        tracemalloc.start()

    try:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        seconds = time.perf_counter() - start
        peak = (
            tracemalloc.get_traced_memory()[1]
            if track_memory
            else 0
        )
    finally:
        if track_memory:
            tracemalloc.stop()

    return result, PerformanceReport(seconds, peak)


def format_performance(report, size_bytes):
    """Format elapsed time, throughput and optional memory usage."""
    speed = (
        size_bytes / report.seconds / (1024 * 1024)
        if report.seconds > 0
        else 0.0
    )

    text = (
        f"Time: {report.seconds:.3f} s | "
        f"Speed: {speed:.2f} MB/s"
    )

    if report.peak_memory:
        text += f" | Peak memory: {format_size(report.peak_memory)}"

    return text
