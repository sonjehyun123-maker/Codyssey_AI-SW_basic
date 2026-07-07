from hashmap import HashMap
from doubly_linked_list import DoublyLinkedList
from min_heap import MinHeap

class RedisDB:
    """HashMap, LRU, TTL 구조를 래핑하여 전체 데이터를 관리하는 메인 엔진"""
    def __init__(self):
        self.db = HashMap()
        self.lru = DoublyLinkedList()
        self.ttl_heap = MinHeap()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0
