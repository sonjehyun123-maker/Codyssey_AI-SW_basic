# -*- coding: utf-8 -*-

import time
import math

from entry import Entry
from doubly_linked_list import DoublyLinkedList
from hashmap import HashMap
from min_heap import MinHeap


class MiniRedis:
    def __init__(self):
        self.table = HashMap()
        self.lru = DoublyLinkedList()
        self.expire_heap = MinHeap()
        self.maxmemory = 0
        self.used_memory = 0
        self.evicted_keys = 0

    @staticmethod
    def _size_of(key, value):
        return len(key.encode('utf-8')) + len(value.encode('utf-8'))

    @staticmethod
    def _is_expired(entry, now):
        return entry.expire_at is not None and entry.expire_at <= now

    def _delete_key_internal(self, key):
        """내부 통합 데이터 삭제 라인"""
        entry = self.table.get(key)
        if entry is None:
            return False
            
        self.used_memory -= self._size_of(entry.key, entry.value)
        self.lru.remove_node(entry)
        self.table.remove(key)
        return True

    def _purge_if_expired(self, key):
        """수동/지연 만료(Lazy Deletion) 검사"""
        entry = self.table.get(key)
        if entry and self._is_expired(entry, time.time()):
            self._delete_key_internal(key)
            return True
        return False
    
    def _sweep_expired_heap(self):
        """능동 만료(Active Expire) 검사"""
        now = time.time()
        while not self.expire_heap.is_empty():
            expire_at, key = self.expire_heap.peek()
            if expire_at > now:
                break
                
            self.expire_heap.pop()
            entry = self.table.get(key)
            if entry and entry.expire_at is not None and entry.expire_at <= now:
                self._delete_key_internal(key)

    def _evict_lru(self):
        """메모리 초과 시 LRU 알고리즘 데이터 청소"""
        while self.maxmemory > 0 and self.used_memory > self.maxmemory and self.lru.size > 0:
            victim_node = self.lru.tail
            if victim_node is None:
                break
            self._delete_key_internal(victim_node.key)
            self.evicted_keys += 1

    # ---------------- Redis 명령어 명세 ----------------

    def cmd_set(self, key, value):
        self._sweep_expired_heap()
        entry_size = self._size_of(key, value)

        if self.maxmemory > 0 and entry_size > self.maxmemory:
            return "(error) OOM command not allowed when used_memory > 'maxmemory'"
        # 기존 존재하는 키일 경우
        existing = self.table.get(key)
        if existing is not None:
            self.used_memory -= self._size_of(existing.key, existing.value)
            existing.value = value
            existing.expire_at = None  # 덮어쓰기 시 기존 TTL 해제 요구사항 준수
            self.used_memory += entry_size
            self.lru.move_to_front(existing)
        # 새로운 키일 경우
        else:
            entry = Entry(key, value)
            self.lru.insert_front(entry)
            self.table.put(key, entry)
            self.used_memory += entry_size

        self._evict_lru()
        return "OK"

    def cmd_get(self, key):
        self._purge_if_expired(key)
        entry = self.table.get(key)
        if entry is None:
            return "(nil)"
            
        self.lru.move_to_front(entry)
        return f'"{entry.value}"'

    def cmd_del(self, key):
        # 만료되었으면 없는 취급하므로 0 반환 규칙 준수
        if self._purge_if_expired(key):
            return "(integer) 0"
        return "(integer) 1" if self._delete_key_internal(key) else "(integer) 0"

    def cmd_exists(self, key):
        self._purge_if_expired(key)
        return "(integer) 1" if self.table.contains(key) else "(integer) 0"

    def cmd_dbsize(self):
        self._sweep_expired_heap()
        return f"(integer) {self.table.size}"

    def cmd_keys(self):
        self._sweep_expired_heap()
        return self.table.keys()

    def cmd_config_set_maxmemory(self, bytes_val):
        self.maxmemory = bytes_val
        self._evict_lru()
        return "OK"

    def cmd_info_memory(self):
        return f"used_memory:{self.used_memory}\nmaxmemory:{self.maxmemory}\nevicted_keys:{self.evicted_keys}"

    def cmd_expire(self, key, seconds):
        self._purge_if_expired(key)
        entry = self.table.get(key)
        if entry is None:
            return "(integer) 0"

        if seconds <= 0:
            self._delete_key_internal(key)
            return "(integer) 1"

        expire_at = time.time() + seconds
        entry.expire_at = expire_at
        self.expire_heap.push((expire_at, key))
        return "(integer) 1"

    def cmd_ttl(self, key):
        self._purge_if_expired(key)
        entry = self.table.get(key)
        if entry is None:
            return "(integer) -2"
        if entry.expire_at is None:
            return "(integer) -1"

        remaining = entry.expire_at - time.time()
        if remaining <= 0:
            self._delete_key_internal(key)
            return "(integer) -2"
        return f"(integer) {math.ceil(remaining)}"