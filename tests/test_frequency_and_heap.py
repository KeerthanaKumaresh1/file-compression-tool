"""Dedicated tests for BL3 (frequency analysis) and BL4 (min heap)."""

import random
import unittest

from compressor.frequency import calculate_frequencies
from compressor.min_heap import MinHeap


class TestFrequencyAnalysis(unittest.TestCase):

    def test_known_example(self):
        self.assertEqual(
            calculate_frequencies(b"AAAABBBCCD"),
            {65: 4, 66: 3, 67: 2, 68: 1},
        )

    def test_total_equals_length(self):
        data = bytes(range(256)) * 3 + b"xyz"
        freq = calculate_frequencies(data)
        self.assertEqual(sum(freq.values()), len(data))
        self.assertEqual(len(freq), 256)

    def test_result_is_sorted_by_byte_value(self):
        self.assertEqual(list(calculate_frequencies(b"zaq")), [97, 113, 122])

    def test_empty_input(self):
        self.assertEqual(calculate_frequencies(b""), {})


class TestMinHeapOrdering(unittest.TestCase):

    def test_pops_in_sorted_order(self):
        rng = random.Random(3)
        values = [rng.randrange(1000) for _ in range(200)]
        heap = MinHeap()
        for v in values:
            heap.push(v, v)
        self.assertEqual(len(heap), 200)
        self.assertEqual([heap.pop()[0] for _ in range(200)], sorted(values))

    def test_equal_priorities_keep_insertion_order(self):
        heap = MinHeap()
        for name in "abcde":
            heap.push(1, name)
        self.assertEqual([heap.pop()[1] for _ in range(5)], list("abcde"))


if __name__ == "__main__":
    unittest.main()
