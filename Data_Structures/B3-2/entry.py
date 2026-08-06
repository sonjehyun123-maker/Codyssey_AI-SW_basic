import hashlib
import time


class Commit:
    """SHA-1 해시(40자리)를 갖는 커밋 노드."""

    def __init__(self, message, author, parents):
        self.message = message
        self.author = author
        self.parents = parents
        self.timestamp = time.time()
        self.hash = self._generate_hash()

    def _generate_hash(self):
        """message+author+parents+timestamp를 SHA-1으로 해시해 40자리 16진수 문자열을 반환한다."""
        content = f"{self.message}{self.author}{self.parents}{self.timestamp}"
        content_bytes = content.encode()
        sha1_object = hashlib.sha1(content_bytes)
        return sha1_object.hexdigest()