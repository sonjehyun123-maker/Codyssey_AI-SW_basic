class Entry:
    """해시맵(체이닝)과 LRU(이중 연결)를 동시에 만족하는 엔트리 노드"""
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.lru_prev = None
        self.lru_next = None
        self.hash_next = None
