from collections import deque

def get_all_commits(hashmap):
    "해시맵 커밋 수집"
    commits = []
    for bucket in hashmap.buckets:
        current = bucket
        while current is not None:
            commits.append(current.commit)
            current = current.next
    return commits

def log(hashmap):
    "위상정렬 / 깊이 탐색"
    all_commits = get_all_commits(hashmap)
    commit_by_hash = {c.hash: c for c in all_commits}
    visited = set()
    result = []

    def visit(commit_hash):
        "재귀적으로 부모 커밋을 방문하여 결과에 추가"
        if commit_hash in visited:
            return
        visited.add(commit_hash)
        commit = commit_by_hash[commit_hash]
        for parent_hash in commit.parents:
            visit(parent_hash)
        result.append(commit)

    for commit in all_commits:
        visit(commit.hash)

    return result

def ancestors(hashmap, start_hash):
    "조상 커밋 탐색"
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
    "무향 그래프 생성"
    all_commits = get_all_commits(hashmap)
    graph = {c.hash: [] for c in all_commits}
    for commit in all_commits:
        for parent_hash in commit.parents:
            graph[commit.hash].append(parent_hash)
            graph[parent_hash].append(commit.hash)
    return graph

def path(hashmap, hash1, hash2):
    "최단 경로 탐색"
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
 