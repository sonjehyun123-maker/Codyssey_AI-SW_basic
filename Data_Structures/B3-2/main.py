import shlex
import time

from Repository import Repository
from graph import log as graph_log, ancestors as graph_ancestors, path as graph_path, get_all_commits
from sort_ import sort_by_date, sort_by_author


"타임스탬프를 읽기 쉬운 문자열로 변환"
def format_time(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


"커밋 해시에 연결된 브랜치 태그를 가져옴"
def branch_tags(repo, commit_hash):
    tags = [name for name, head_hash in repo.branches.items() if head_hash == commit_hash]
    if not tags:
        return ""
    return " [" + ", ".join(tags) + "]"


"커밋 정보를 화면에 출력"
def print_commit(repo, commit):
    tags = branch_tags(repo, commit.hash)
    print(f"commit {commit.hash} ({commit.author}, {format_time(commit.timestamp)}){tags}")
    print(commit.message)


"저장소 초기화 명령 처리"
def handle_init(repo, args):
    if len(args) != 1:
        print("Invalid args")
        return
    repo.init(args[0])
    print("Initialized repository.")
    print(f"Current branch: {repo.head}")
    print(f"Current user: {repo.current_user}")


"새 브랜치를 생성하는 명령 처리"
def handle_branch(repo, args):
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return
    branch_name = args[0]
    repo.branch(branch_name)
    print(f"Created branch: {branch_name}")


"브랜치를 전환하는 명령 처리"
def handle_switch(repo, args):
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return
    branch_name = args[0]
    if branch_name not in repo.branches:
        print(f"Unknown branch: {branch_name}")
        return
    repo.switch(branch_name)
    print(f"Switched to branch: {branch_name}")


"커밋을 생성하는 명령 처리"
def handle_commit(repo, args):
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return
    message = args[0]
    commit = repo.commit(message)
    print(f"[{repo.head} {commit.hash}] {message}")


"로그 출력과 정렬 옵션 처리"
def handle_log(repo, args):
    if repo.head is None:
        print("Invalid args")
        return

    if len(args) == 0:
        commits = graph_log(repo.hashmap)
    elif len(args) == 1 and args[0].startswith("--sort-by="):
        sort_key = args[0].split("=", 1)[1]
        all_commits = get_all_commits(repo.hashmap)
        if sort_key == "date":
            commits = sort_by_date(all_commits)
        elif sort_key == "author":
            commits = sort_by_author(all_commits)
        else:
            print("Invalid args")
            return
    else:
        print("Invalid args")
        return

    for commit in commits:
        print_commit(repo, commit)


"두 커밋 사이의 경로를 찾는 명령 처리"
def handle_path(repo, args):
    if repo.head is None or len(args) != 2:
        print("Invalid args")
        return
    hash1, hash2 = args
    if repo.hashmap.get(hash1) is None:
        print(f"Unknown commit: {hash1}")
        return
    if repo.hashmap.get(hash2) is None:
        print(f"Unknown commit: {hash2}")
        return

    result = graph_path(repo.hashmap, hash1, hash2)
    if result is None:
        print("No path")
    else:
        print("Path: " + " -> ".join(result))


"지정 커밋의 조상 커밋을 출력하는 명령 처리"
def handle_ancestors(repo, args):
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return
    target_hash = args[0]
    if repo.hashmap.get(target_hash) is None:
        print(f"Unknown commit: {target_hash}")
        return

    result = sorted(graph_ancestors(repo.hashmap, target_hash))
    if not result:
        print("No ancestors")
        return
    for commit_hash in result:
        commit = repo.hashmap.get(commit_hash)
        print_commit(repo, commit)


"커밋 메시지나 작성자 검색을 처리하는 명령"
def handle_search(repo, args):
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return

    if args[0].startswith("--author="):
        author = args[0].split("=", 1)[1]
        hashes = repo.index.search_author(author)
    else:
        keyword = args[0]
        hashes = repo.index.search_keyword(keyword)

    print(f"Found {len(hashes)} commit(s):")
    print()
    for commit_hash in hashes:
        commit = repo.hashmap.get(commit_hash)
        print(f"- {commit.hash}: {commit.message}")


COMMAND_TABLE = {
    "INIT": handle_init,
    "BRANCH": handle_branch,
    "SWITCH": handle_switch,
    "COMMIT": handle_commit,
    "LOG": handle_log,
    "PATH": handle_path,
    "ANCESTORS": handle_ancestors,
    "SEARCH": handle_search,
}


def run():
    repo = Repository()
    while True:
        try:
            line = input("mini-git> ")
        except EOFError:
            break

        line = line.strip()
        if not line:
            continue

        try:
            tokens = shlex.split(line)
        except ValueError:
            print("Invalid args")
            continue

        if not tokens:
            continue

        command = tokens[0].upper()
        args = tokens[1:]

        if command in ("EXIT", "QUIT"):
            break

        handler = COMMAND_TABLE.get(command)
        if handler is None:
            print("Invalid args")
            continue

        handler(repo, args)


if __name__ == "__main__":
    run()