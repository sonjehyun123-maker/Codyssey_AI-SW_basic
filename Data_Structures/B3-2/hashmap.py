class Node:
    """해시맵 버킷 내 체이닝을 위해 Commit을 감싸는 연결 노드."""

    def __init__(self, commit):
        self.commit = commit
        self.next = None


class HashMap:
    """hash를 키로 Commit을 저장하는 체이닝 방식 해시맵. 버킷 개수는 고정(리해시 미구현)."""

    def __init__(self, bucket_count=16):
        self.bucket_count = bucket_count
        self.buckets = [None] * bucket_count

    def _hash_index(self, key):
        """문자열 key를 djb2 스타일로 해싱해 버킷 인덱스를 계산한다."""
        hash_value = 0
        for char in key:
            hash_value = hash_value * 33 + ord(char)
        return hash_value % self.bucket_count

    def put(self, commit):
        """Commit을 해시맵에 저장한다. 같은 hash가 이미 있으면 commit.hash가 유일해질 때까지 extend_hash()로 재시도한다."""
        while self.get(commit.hash) is not None:
            commit.extend_hash()
        index = self._hash_index(commit.hash)
        new_node = Node(commit)
        new_node.next = self.buckets[index]
        self.buckets[index] = new_node

    def get(self, key):
        """hash로 저장된 Commit을 조회한다. 없으면 None을 반환한다."""
        index = self._hash_index(key)
        current = self.buckets[index]
        while current is not None:
            if current.commit.hash == key:
                return current.commit
            current = current.next
        return None