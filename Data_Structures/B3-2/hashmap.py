class Node:
    """체이닝용 노드."""

    def __init__(self, commit):
        self.commit = commit
        self.next = None


class HashMap:
    """앞 2자리(16^2=256가지)를 버킷 번호로 직접 쓰는 해시맵.
    SHA-1 출력은 이미 균등하게 흩어지므로 별도 해시 함수(djb2 등) 없이 접두사를 그대로 씀."""

    def __init__(self, bucket_count=256):
        self.bucket_count = bucket_count
        self.buckets = [None] * bucket_count

    def _hash_index(self, key):
        """key의 앞 2자리(16진수)를 그대로 버킷 번호로 쓴다."""
        return int(key[:2], 16)

    def put(self, commit):
        """Commit을 저장한다."""
        index = self._hash_index(commit.hash)
        new_node = Node(commit)
        new_node.next = self.buckets[index]
        self.buckets[index] = new_node

    def get(self, key):
        """전체 hash로 Commit을 조회한다."""
        index = self._hash_index(key)
        current = self.buckets[index]
        while current is not None:
            if current.commit.hash == key:
                return current.commit
            current = current.next
        return None

    def find_by_prefix(self, prefix):
        """짧은 접두사로 시작하는 모든 Commit을 찾는다.
        접두사가 2자리 이상이면 해당 버킷 하나만 확인(빠름), 아니면 전체를 훑는다."""
        if len(prefix) >= 2:
            try:
                index = self._hash_index(prefix)
            except ValueError:
                return []
            buckets_to_check = [self.buckets[index]]
        else:
            buckets_to_check = self.buckets

        matches = []
        for bucket in buckets_to_check:
            node = bucket
            while node is not None:
                if node.commit.hash.startswith(prefix):
                    matches.append(node.commit)
                node = node.next
        return matches