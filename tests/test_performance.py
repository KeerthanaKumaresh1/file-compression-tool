
import unittest
import time

from compressor.performance import (
    PerformanceReport,
    format_performance,
    measure,
)


class TestPerformance(unittest.TestCase):
    def test_returns_result_and_time(self):
        result, report = measure(lambda x: x * 2, 21)
        self.assertEqual(result, 42)
        self.assertGreaterEqual(report.seconds, 0)
        self.assertEqual(report.peak_memory, 0)

    def test_measures_elapsed_time(self):
        _, report = measure(time.sleep, 0.05)
        self.assertGreaterEqual(report.seconds, 0.04)

    def test_memory_tracking(self):
        _, report = measure(
            lambda: bytearray(1_000_000),
            track_memory=True,
        )
        self.assertGreater(report.peak_memory, 500_000)

    def test_format(self):
        text = format_performance(
            PerformanceReport(0.5, 2048),
            1024 * 1024,
        )
        self.assertIn("2.00 MB/s", text)
        self.assertIn("2.00 KB", text)


if __name__ == "__main__":
    unittest.main()

