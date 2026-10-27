"""BL4 - Min Heap (array based, written by hand - no heapq)."""


class MinHeap:
    """Min-heap of (priority, item) pairs.

    Equal priorities come out in the order they were pushed, so the Huffman
    tree is built identically every time (the decoder relies on this).
    """

    def __init__(self):
        self._data = []      # list of (priority, order, item)
        self._counter = 0    # insertion order, used to break ties

    def __len__(self):
        return len(self._data)

    def is_empty(self):
        return not self._data

    def push(self, priority, item):
        self._data.append((priority, self._counter, item))
        self._counter += 1
        self._sift_up(len(self._data) - 1)

    def pop(self):
        """Remove and return the (priority, item) with the smallest priority."""
        if not self._data:
            raise IndexError("pop from an empty heap")
        top = self._data[0]
        last = self._data.pop()
        if self._data:
            self._data[0] = last
            self._sift_down(0)
        return top[0], top[2]

    def peek(self):
        if not self._data:
            raise IndexError("peek at an empty heap")
        return self._data[0][0], self._data[0][2]

    def _key(self, index):
        return self._data[index][0], self._data[index][1]

    def _swap(self, i, j):
        self._data[i], self._data[j] = self._data[j], self._data[i]

    def _sift_up(self, index):
        while index > 0:
            parent = (index - 1) // 2
            if self._key(index) < self._key(parent):
                self._swap(index, parent)
                index = parent
            else:
                break

    def _sift_down(self, index):
        size = len(self._data)
        while True:
            smallest = index
            left, right = 2 * index + 1, 2 * index + 2
            if left < size and self._key(left) < self._key(smallest):
                smallest = left
            if right < size and self._key(right) < self._key(smallest):
                smallest = right
            if smallest == index:
                break
            self._swap(index, smallest)
            index = smallest