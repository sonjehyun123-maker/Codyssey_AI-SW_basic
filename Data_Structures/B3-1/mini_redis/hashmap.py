# 해시맵
from entry import Entry

class HashMap: 
    def __init__(self): 
        self.bucket_size = 8 
        self.bucket = [None] * self.bucket_size 
        self.size = 0 
        self.load_factor = 0.75

    def hash_function(self, key):
        h = 0
        for ch in key:
            h = ((h*31)+ ord(ch))
        return h
    
    def index_for(self, key, value):
        return self.hash_function(key) % self.bucket_size
    
    def put(self, key):
        idx = self.index_for(key)
        current = self.bucket[idx]
        while current is not None:
            if current.key == key:
                return current
            current = current.hash_next
        return None
