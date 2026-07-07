from entry import Entry

class HashMap:
    """내장 dict 없이 구현하는 체이닝 방식 해시맵"""
    def __init__(self):
        self.bucket_size = 8
        self.bucket = [None] * self.bucket_size
        self.size = 0
        self.load_factor_threshold = 0.75
