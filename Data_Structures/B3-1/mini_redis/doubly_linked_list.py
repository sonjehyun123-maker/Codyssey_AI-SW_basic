from entry import Entry

class DoublyLinkedList:
    """LRU 캐시 순서를 관리하는 이중 연결 리스트"""
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def insert_front(self, entry: Entry):
        """이미 생성된 Entry 객체를 리스트의 맨 앞에 삽입합니다. O(1)"""
        if self.size == 0:
            self.head = entry
            self.tail = entry
            entry.lru_prev = None
            entry.lru_next = None
        else: 
            entry.lru_next = self.head
            self.head.lru_prev = entry
            self.head = entry
            entry.lru_prev = None
        self.size += 1
        return entry
        
    def insert_back(self, entry: Entry):
        """이미 생성된 Entry 객체를 리스트의 맨 뒤에 삽입합니다. O(1)"""
        if self.size == 0:
            self.head = entry
            self.tail = entry
            entry.lru_prev = None
            entry.lru_next = None
        else: 
            entry.lru_prev = self.tail
            self.tail.lru_next = entry
            self.tail = entry
            entry.lru_next = None
        self.size += 1
        return entry

    def remove_front(self):
        """리스트의 맨 앞 엔트리를 제거하고 반환합니다. O(1)"""
        if self.size == 0:
            return None
        
        removed_entry = self.head
        if self.size == 1:
            self.head = None
            self.tail = None
        else:
            self.head = self.head.lru_next
            self.head.lru_prev = None
            
        removed_entry.lru_next = None
        removed_entry.lru_prev = None
        self.size -= 1
        return removed_entry

    def remove_back(self):
        """리스트의 맨 뒤 엔트리를 제거하고 반환합니다. O(1)"""
        if self.size == 0:
            return None
        
        removed_entry = self.tail
        if self.size == 1:
            self.head = None
            self.tail = None
        else:
            self.tail = self.tail.lru_prev
            self.tail.lru_next = None
            
        removed_entry.lru_next = None
        removed_entry.lru_prev = None
        self.size -= 1
        return removed_entry

    def remove_node(self, entry: Entry):
        """지정된 엔트리를 리스트에서 안전하게 제거합니다. O(1)"""
        if self.size == 0 or entry is None:
            return
        if entry is self.head:
            self.remove_front()
            return
        if entry is self.tail:
            self.remove_back()
            return
            
        entry.lru_prev.lru_next = entry.lru_next
        entry.lru_next.lru_prev = entry.lru_prev
        entry.lru_prev = None
        entry.lru_next = None
        self.size -= 1

    def move_to_front(self, entry: Entry):
        """지정된 엔트리를 맨 앞으로 이동시킵니다. O(1)"""
        if self.size <= 1 or entry is self.head:
            return

        if entry.lru_prev:
            entry.lru_prev.lru_next = entry.lru_next

        if entry.lru_next:
            entry.lru_next.lru_prev = entry.lru_prev
        else:
            self.tail = entry.lru_prev

        entry.lru_next = self.head
        entry.lru_prev = None

        self.head.lru_prev = entry
        self.head = entry