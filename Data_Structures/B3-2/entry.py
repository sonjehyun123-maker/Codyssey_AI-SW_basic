import hashlib
import time


class Commit:
    """message, author, parents, timestamp로 SHA-1 해시를 계산하는 커밋 노드."""

    def __init__(self, message, author, parents):
        self.message = message
        self.author = author
        self.parents = parents
        self.timestamp = time.time()
        self.full_hash = self._generate_full_hash()
        self.hash_length = 4
        self.hash = self.full_hash[:self.hash_length]

    def _generate_full_hash(self):
        """message+author+parents+timestamp를 SHA-1으로 해시해 40자리 16진수 문자열을 반환한다."""
        content = f"{self.message}{self.author}{self.parents}{self.timestamp}"
        content_bytes = content.encode()
        sha1_object = hashlib.sha1(content_bytes)
        full_hash = sha1_object.hexdigest()
        return full_hash

    def extend_hash(self):
        """해시 충돌 시 표시 자릿수를 1 늘려 full_hash에서 더 긴 접두사를 사용한다. 상한 없음(최대 40자리, 40자리끼리도 겹치면 SHA-1 자체 충돌이라 별도 처리 안 함)."""
        self.hash_length += 1
        self.hash = self.full_hash[:self.hash_length]