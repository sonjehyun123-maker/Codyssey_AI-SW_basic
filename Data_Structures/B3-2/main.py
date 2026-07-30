import shlex
import time

from repository import Repository
from graph import log as graph_log, ancestors as graph_ancestors, path as graph_path, get_all_commits
from sort import sort_by_date, sort_by_author


def format_time(timestamp):
    """타임스탬프를 'YYYY-MM-DD HH:MM:SS' 형식의 문자열로 변환한다."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def branch_tags(repo, commit_hash):
    """주어진 커밋 해시에 연결된 브랜치 태그를 찾아 문자열로 반환한다. 태그가 없으면 빈 문자열을 반환한다."""
    tags = [name for name, head_hash in repo.branches.items() if head_hash == commit_hash]
    if not tags:
        return ""
    return " [" + ", ".join(tags) + "]"


def print_commit(repo, commit):
    """커밋 정보(해시, 저자, 시간, 브랜치 태그, 메시지)를 형식에 맞춰 출력한다."""
    tags = branch_tags(repo, commit.hash)
    print(f"commit {commit.hash} ({commit.author}, {format_time(commit.timestamp)}){tags}")
    print(commit.message)


def handle_init(repo, args):
    """INIT 처리. 저장소를 초기화하고 현재 브랜치와 사용자 정보를 출력한다."""
    if len(args) != 1:
        print("Invalid args")
        return
    repo.init(args[0])
    print("Initialized repository.")
    print(f"Current branch: {repo.head}")
    print(f"Current user: {repo.current_user}")


def handle_branch(repo, args):
    """BRANCH 처리. 이미 존재하는 브랜치 이름이면 거부한다(실제 git branch와 동일하게 덮어쓰기 방지)."""
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return
    branch_name = args[0]
    if branch_name in repo.branches:
        print(f"Branch already exists: {branch_name}")
        return
    repo.branch(branch_name)
    print(f"Created branch: {branch_name}")


def handle_switch(repo, args):
    """SWITCH 처리. 지정된 브랜치로 전환한다. 존재하지 않는 브랜치면 오류를 출력한다."""
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return
    branch_name = args[0]
    if branch_name not in repo.branches:
        print(f"Unknown branch: {branch_name}")
        return
    repo.switch(branch_name)
    print(f"Switched to branch: {branch_name}")


def handle_commit(repo, args):
    """COMMIT 처리. 새로운 커밋을 생성하고 커밋 정보를 출력한다."""
    if repo.head is None or len(args) != 1:
        print("Invalid args")
        return
    message = args[0]
    commit = repo.commit(message)
    print(f"[{repo.head} {commit.hash}] {message}")


def handle_log(repo, args):
    """LOG 처리. 인자 없으면 위상 정렬, --sort-by=date|author면 병합 정렬. 허용되지 않는 정렬 키는 Invalid args."""
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


def handle_path(repo, args):
    """PATH 처리. 경로 없으면 'No path' 출력, 있으면 'Path: h1 -> h2 -> ...' 형식으로 출력."""
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


def handle_ancestors(repo, args):
    """ANCESTORS 처리. graph.ancestors()가 반환한 set을 hash 사전순으로 정렬해 출력한다."""
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


def handle_search(repo, args):
    """SEARCH 처리. 저자명 또는 키워드로 커밋을 검색해 매칭된 커밋 목록을 출력한다."""
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
    """미니-깃 클라이언트를 실행한다. 사용자 입력을 받아 명령을 처리하는 REPL 루프를 시작한다."""
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