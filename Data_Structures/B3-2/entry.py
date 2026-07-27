import hashlib
import time


class Commit:
    def __init__(self, message, author, parents):
        self.message = message
        self.author = author
        self.parents = parents
        self.timestamp = time.time()
        self.full_hash = self._generate_full_hash()
        self.hash_length = 4
        self.hash = self.full_hash[:self.hash_length]

    def _generate_full_hash(self):
        content = f"{self.message}{self.author}{self.parents}{self.timestamp}"
        content_bytes = content.encode()
        sha1_object = hashlib.sha1(content_bytes)
        full_hash = sha1_object.hexdigest()
        return full_hash

    def extend_hash(self):
        self.hash_length += 1
        self.hash = self.full_hash[:self.hash_length]