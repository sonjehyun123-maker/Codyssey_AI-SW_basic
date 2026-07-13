# -*- coding: utf-8 -*-

class MinHeap:
    def __init__(self):
        self.data = []

    def size(self):
        return len(self.data)

    def is_empty(self):
        return len(self.data) == 0

    def peek(self):
        return self.data[0] if self.data else None

    def push(self, item):
        """item = (expire_at, key)"""
        self.data.append(item)
        self._heapify_up(len(self.data) - 1)

    def pop(self):
        if not self.data:
            return None
        top = self.data[0]
        last_item = self.data.pop()
        if self.data:
            self.data[0] = last_item
            self._heapify_down(0)
        return top

    def _heapify_up(self, idx):
        while idx > 0:
            parent = (idx - 1) // 2
            if self.data[idx][0] < self.data[parent][0]:
                self.data[idx], self.data[parent] = self.data[parent], self.data[idx]
                idx = parent
            else:
                break

    def _heapify_down(self, idx):
        n = len(self.data)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            smallest = idx

            if left < n and self.data[left][0] < self.data[smallest][0]:
                smallest = left
            if right < n and self.data[right][0] < self.data[smallest][0]:
                smallest = right

            if smallest == idx:
                break

            self.data[idx], self.data[smallest] = self.data[smallest], self.data[idx]
            idx = smallest