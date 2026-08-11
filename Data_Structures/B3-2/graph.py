from collections import deque
from sort import sort_by_date


def get_all_commits(hashmap):
    """해시맵의 모든 Commit을 반환한다."""
    commits = []
    for bucket in hashmap.buckets:
        current = bucket
        while current is not None:
            commits.append(current.commit)
            current = current.next
    return commits


def log(hashmap):
    """부모 우선 위상 정렬로 커밋을 반환한다. 리프를 날짜순으로 방문하고, 각 리프의 조상을 한 번에 가져와 브랜치별로 묶는다."""
    all_commits = get_all_commits(hashmap)
    commit_by_hash = {c.hash: c for c in all_commits}

    parent_hashes = set()
    for commit in all_commits:
        for parent_hash in commit.parents:
            parent_hashes.add(parent_hash)
    leaves = sort_by_date([c for c in all_commits if c.hash not in parent_hashes])

    visited = set()
    result = []

    def visit(commit_hash):
        if commit_hash in visited:
            return
        visited.add(commit_hash)
        commit = commit_by_hash[commit_hash]
        for parent_hash in commit.parents:
            visit(parent_hash)
        result.append(commit)

    for leaf in leaves:
        visit(leaf.hash)

    return result


def ancestors(hashmap, start_hash):
    """start_hash의 모든 조상 hash를 반환한다."""
    commit_by_hash = {c.hash: c for c in get_all_commits(hashmap)}
    visited = set()
    queue = deque([start_hash])

    while queue:
        current_hash = queue.popleft()
        commit = commit_by_hash[current_hash]
        for parent_hash in commit.parents:
            if parent_hash not in visited:
                visited.add(parent_hash)
                queue.append(parent_hash)

    return visited


def build_undirected_graph(hashmap):
    """parents를 무방향 간선으로 변환한다."""
    all_commits = get_all_commits(hashmap)
    graph = {c.hash: [] for c in all_commits}
    for commit in all_commits:
        for parent_hash in commit.parents:
            graph[commit.hash].append(parent_hash)
            graph[parent_hash].append(commit.hash)
    return graph


def path(hashmap, hash1, hash2):
    """두 커밋 사이 최단 경로를 찾는다."""
    graph = build_undirected_graph(hashmap)
    queue = deque([[hash1]])
    visited = {hash1}
    shortest_paths = []
    shortest_length = None

    while queue:
        current_path = queue.popleft()
        if shortest_length is not None and len(current_path) > shortest_length:
            break
        last_node = current_path[-1]
        if last_node == hash2:
            shortest_length = len(current_path)
            shortest_paths.append(current_path)
            continue
        for neighbor in sorted(graph.get(last_node, [])):
            if neighbor not in visited or neighbor == hash2:
                new_path = current_path + [neighbor]
                queue.append(new_path)
        visited.add(last_node)

    if not shortest_paths:
        return None

    shortest_paths.sort(key=lambda p: "->".join(p))
    return shortest_paths[0]