import hashlib
import time

class Commit:
    def __init__(self, message, author, parents):
        self.message = message
        self.author = author
        self.parents = parents
        self.timestamp = time.time()
        self.hash = self._generate_hash()

    def _generate_hash(self):
        content = f"{self.message}{self.author}{self.parents}{self.timestamp}"
        content_bytes = content.encode()
        sha1_object = hashlib.sha1(content_bytes)
        full_hash = sha1_object.hexdigest()
        short_hash = full_hash[:4]
        return short_hash