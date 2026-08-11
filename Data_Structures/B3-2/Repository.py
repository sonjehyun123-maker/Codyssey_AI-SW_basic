from entry import Commit
from hashmap import HashMap
from git_index import InvertedIndex


class Repository:
    """저장소 상태(브랜치, HEAD) 관리."""

    def __init__(self):
        self.branches = {}
        self.head = None
        self.current_user = None
        self.hashmap = HashMap()
        self.index = InvertedIndex()

    def init(self, user_name):
        """저장소를 초기화한다."""
        if self.head is not None:
            self.current_user = user_name
            return
        self.current_user = user_name
        self.branches = {"main": None}
        self.head = "main"

    def branch(self, branch_name):
        """현재 HEAD가 가리키는 커밋을 가리키는 새 브랜치를 만든다."""
        current_commit_hash = self.branches.get(self.head)
        if current_commit_hash is None:
            raise ValueError("Cannot create branch before the current branch has a commit")
        self.branches[branch_name] = current_commit_hash

    def switch(self, branch_name):
        """HEAD를 지정한 브랜치로 이동한다."""
        self.head = branch_name

    def commit(self, message):
        """새 커밋을 만들고 해시맵·역색인·브랜치를 갱신한다."""
        parent_hash = self.branches[self.head]
        if parent_hash is None:
            parents = []
        else:
            parents = [parent_hash]

        new_commit = Commit(message, self.current_user, parents)
        self.hashmap.put(new_commit)
        self.index.add_commit(new_commit)
        self.branches[self.head] = new_commit.hash
        return new_commit