from hashmap import HashMap
from doubly_linked_list import DoublyLinkedList
from min_heap import MinHeap

class RedisDB:
    def __init__(self):
        self.db = HashMap()
        self.lru = DoublyLinkedList()
        self.ttl_heap = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0              # 0 = 무제한
        self.evicted_keys = 0
