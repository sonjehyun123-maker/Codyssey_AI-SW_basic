class Node:
    def __init__(self, commit):
        self.commit = commit
        self.next = None


class HashMap:
    def __init__(self, bucket_count=16):
        self.bucket_count = bucket_count
        self.buckets = [None] * bucket_count

    def _hash_index(self, key):
        hash_value = 0
        for char in key:
            hash_value = hash_value * 33 + ord(char)
        return hash_value % self.bucket_count

    def put(self, commit):
        index = self._hash_index(commit.hash)
        new_node = Node(commit)
        new_node.next = self.buckets[index]
        self.buckets[index] = new_node

    def get(self, key):
        index = self._hash_index(key)
        current = self.buckets[index]
        while current is not None:
            if current.commit.hash == key:
                return current.commit
            current = current.next
        return None