class InvertedIndex:
    def __init__(self):
        # 키워드 및 작성자 역색인 사전 초기화
        self.keyword_index = {}
        self.author_index = {}

    def add_commit(self, commit):
        tokens = commit.message.lower().split()
        # 커밋 메시지의 각 단어를 커밋 해시로 색인화
        for token in tokens:
            if token not in self.keyword_index:
                self.keyword_index[token] = []
            self.keyword_index[token].append(commit.hash)

        # 작성자 이름으로 커밋 해시 색인화
        if commit.author not in self.author_index:
            self.author_index[commit.author] = []
        self.author_index[commit.author].append(commit.hash)

    def search_keyword(self, keyword):
        # 키워드에 해당하는 커밋 해시 반환
        return self.keyword_index.get(keyword.lower(), [])

    def search_author(self, author):
        # 작성자에 해당하는 커밋 해시 반환
        return self.author_index.get(author, [])