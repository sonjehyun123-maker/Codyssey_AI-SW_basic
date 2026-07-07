# 엔트리
class Entry:
    def __init__(self, key, value):
        self.key = key
        self.value = value

        self.lru_prev = None
        self.lru_next = None

        self.hash_next = None
