from entry import Commit
from hashmap import HashMap


class Repository:
    def __init__(self):
        self.branches = {}
        self.head = None
        self.current_user = None
        self.hashmap = HashMap()

    def init(self, user_name):
        self.current_user = user_name
        self.branches = {"main": None}
        self.head = "main"

    def branch(self, branch_name):
        current_commit_hash = self.branches[self.head]
        self.branches[branch_name] = current_commit_hash

    def switch(self, branch_name):
        self.head = branch_name

    def commit(self, message):
        parent_hash = self.branches[self.head]
        if parent_hash is None:
            parents = []
        else:
            parents = [parent_hash]

        new_commit = Commit(message, self.current_user, parents)
        self.hashmap.put(new_commit)
        self.branches[self.head] = new_commit.hash
        return new_commit