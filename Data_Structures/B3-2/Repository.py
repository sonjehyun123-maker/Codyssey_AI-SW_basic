from entry import Commit
from hashmap import HashMap
from git_index import InvertedIndex


class Repository:
    def __init__(self):
        "저장소 객체 초기화"
        self.branches = {}
        self.head = None
        self.current_user = None
        self.hashmap = HashMap()
        self.index = InvertedIndex()

    def init(self, user_name):
        "저장소 초기화 및 기본 브랜치(main) 설정"
        if self.head is not None:
            self.current_user = user_name
            return
        self.current_user = user_name
        self.branches = {"main": None}
        self.head = "main"

    def branch(self, branch_name):
        "현재 브랜치에서 새 브랜치를 생성"
        current_commit_hash = self.branches[self.head]
        self.branches[branch_name] = current_commit_hash

    def switch(self, branch_name):
        "현재 작업 중인 브랜치를 변경"
        self.head = branch_name

    def commit(self, message):
        "새 커밋을 생성하고 해시맵과 역색인에 저장"
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