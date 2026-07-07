# 해시맵
from entry import Entry

class HashMap: 
    def __init__(self): 
        self.bucket_size = 8 
        self.bucket = [None] * self.bucket_size 
        self.size = 0 
        self.load_factor = 0.75

    def _hash(self, key):
        h = 0
        for ch in key:
            h = ((h*31)+ ord(ch))
        return h
    
    def index_for(self, key, capacity=None):
        capacity = capacity if capacity is not None else self.bucket_size
        return self._hash(key) % capacity
    
    def put(self, key, entry):
        idx = self.index_for(key)
        # 1. 동일 key 존재 시 값 업데이트
        current = self.bucket[idx]
        while current is not None:
            if current.key == key:
                current.value = entry.value
                return current
            current = current.hash_next

        # 2. 신규 데이터는 체인 맨 앞에 삽입
        entry.hash_next = self.bucket[idx]
        self.bucket[idx] = entry
        self.size += 1

        # 3. 로드 팩터 검사 후 확장
        if (self.size / self.bucket_size) > self.load_factor:
            self._resize()

    def get(self, key):
        idx = self.index_for(key, self.bucket_size)
        current = self.bucket[idx]
        while current is not None:
            if current.key == key:
                return current
            current = current.hash_next
        return None
    
    def contains(self, key):
        return self.get(key) is not None
    
    def remove(self, key):
        idx = self.index_for(key, self.bucket_size)
        current = self.bucket[idx]
        prev = None
        
        while current is not None:
            if current.key == key:
                if prev is None:
                    self.bucket[idx] = current.hash_next
                else:
                    prev.hash_next = current.hash_next
                current.hash_next = None
                self.size -= 1
                return True
            prev = current
            current = current.hash_next
        return False
    
    def _resize(self):
        new_capacity = self.bucket_size * 2
        new_bucket = [None] * new_capacity

        for i in range(self.bucket_size):
            current = self.bucket[i]
            while current is not None:
                next_node = current.hash_next
                
                new_idx = self.index_for(current.key, new_capacity)
                current.hash_next = new_bucket[new_idx]
                new_bucket[new_idx] = current
                
                current = next_node

        self.bucket = new_bucket
        self.bucket_size = new_capacity

    def keys(self):
        result = []
        for i in range(self.bucket_size):
            current = self.bucket[i]
            while current is not None:
                result.append(current.key)
                current = current.hash_next
        return result