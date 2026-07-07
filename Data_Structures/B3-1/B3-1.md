# Mini Redis 구축 - 학습 정리

## 1. 개요

Redis가 빠른 이유인 내부 자료구조(해시맵, 이중 연결 리스트, 힙)를 직접 구현하고,
이를 조합해서 **LRU 캐시**와 **TTL 만료**가 동작하는 CLI 기반 Mini Redis를 만든 과제.

**제약사항**: `dict`, `set`, `collections` 사용 금지 → 해시맵도 배열(`list`) 기반으로 직접 구현.

**파일 구조 (6개, 각 자료구조 독립 모듈)**

```
entry.py               # 공유 데이터 모델 (해시맵/LRU가 같이 참조)
doubly_linked_list.py   # 이중 연결 리스트 (LRU 순서 관리)
hashmap.py              # 해시맵 (체이닝 방식)
min_heap.py             # 최소 힙 (TTL 만료 관리)
redis_db.py             # 위 3개 조립하는 엔진 (MiniRedis 클래스)
main.py                 # REPL / 파싱 / 출력 포맷
```

---

## 2. 요구사항 ↔ 구현 매핑

| 요구사항 | 구현 위치 |
|---|---|
| 이중 연결 리스트 O(1) 연산 | `doubly_linked_list.py` |
| 해시맵 체이닝 + 로드팩터 0.75 확장 | `hashmap.py` |
| 최소 힙 (expire_at, key) | `min_heap.py` |
| SET/GET/DEL/EXISTS/DBSIZE/KEYS | `redis_db.py` cmd_* 메서드 |
| CONFIG SET maxmemory / INFO memory | `redis_db.py` cmd_config_set_maxmemory / cmd_info_memory |
| EXPIRE / TTL | `redis_db.py` cmd_expire / cmd_ttl |
| CLI REPL | `main.py` |

---

## 3. 파일별 핵심 로직

### 3-1. `entry.py` — 공유 데이터 모델

세 자료구조가 각자 다른 목적으로 참조하는 값 하나를 표현. 해시맵 체이닝용 `hash_next`와
LRU 순서용 `lru_prev`/`lru_next`를 **한 객체에 통합**해서, Entry 자신이 곧 DLL의 노드 역할도 겸함.

```python
class Entry:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.expire_at = None      # TTL 없으면 None

        self.lru_prev = None       # DLL 순서 관리용
        self.lru_next = None

        self.hash_next = None      # 해시맵 체이닝용
```

### 3-2. `doubly_linked_list.py` — LRU 순서 관리

별도의 Node 클래스 없이 `Entry` 자체를 노드로 사용. `head`=MRU(최근 사용), `tail`=LRU(오래된 것).

```python
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
```

- 앞뒤 포인터만 갈아끼우는 방식이라 리스트 길이와 무관하게 **O(1)**.
- GET 성공 시, SET으로 값 갱신 시 이 메서드로 MRU 갱신.

### 3-3. `hashmap.py` — 체이닝 해시맵

```python
def _hash(self, key):
    h = 0
    for ch in key:
        h = ((h * 31) + ord(ch))
    return h

def put(self, key, entry):
    idx = self.index_for(key)
    current = self.bucket[idx]
    while current is not None:
        if current.key == key:
            current.value = entry.value   # 같은 key면 값만 갱신
            return current
        current = current.hash_next

    entry.hash_next = self.bucket[idx]    # 체인 맨 앞에 삽입
    self.bucket[idx] = entry
    self.size += 1

    if (self.size / self.bucket_size) > self.load_factor:
        self._resize()
```

- 해시 함수: 31 곱하는 다항 해시 (Java `String.hashCode()`랑 같은 방식, 31이 소수라 분포 안정적).
- 충돌 시 `hash_next`로 체이닝, 로드팩터(0.75) 넘으면 `_resize()`로 버킷 2배 확장 + 전체 재해싱.

### 3-4. `min_heap.py` — TTL 관리용 최소 힙

```python
def _heapify_up(self, idx):
    while idx > 0:
        parent = (idx - 1) // 2
        if self.data[idx][0] < self.data[parent][0]:
            self.data[idx], self.data[parent] = self.data[parent], self.data[idx]
            idx = parent
        else:
            break
```

- 배열 기반 완전 이진트리. `(expire_at, key)` 튜플을 push하면 만료 시각이 가장 빠른 게 항상 root.
- 삭제된 키의 heap 항목은 그대로 두고(lazy), `redis_db.py`에서 pop할 때 "현재도 유효한 만료 정보인지" 재검증.

### 3-5. `redis_db.py` — 세 자료구조를 접착하는 엔진

```python
def _evict_lru(self):
    """메모리 초과 시 LRU 알고리즘 데이터 청소"""
    while self.maxmemory > 0 and self.used_memory > self.maxmemory and self.lru.size > 0:
        victim_node = self.lru.tail          # LRU = 맨 뒤
        if victim_node is None:
            break
        self._delete_key_internal(victim_node.key)
        self.evicted_keys += 1
```

- `used_memory` 계산: `len(utf8(key)) + len(utf8(value))`의 합.
- SET 후 `maxmemory` 초과 시 tail(LRU)부터 하나씩 삭제.

### 3-6. `main.py` — REPL

```python
SPECS = {
    "SET": (3, "(error) ERR wrong number of arguments for 'SET' command"),
    "GET": (2, "(error) ERR wrong number of arguments for 'GET' command"),
    ...
}
if cmd in SPECS:
    expected_len, err_msg = SPECS[cmd]
    if len(tokens) != expected_len:
        return err_msg
```

- 명령어별 예상 토큰 개수를 미리 정의해두고, 다르면 표준화된 에러 메시지 리턴.
- 큰따옴표로 감싼 인자도 하나로 인식하는 간이 파서(`split_arguments`) 포함.

---

## 4. SET / GET 실행 흐름 (파일 간 호출 순서)

### SET name jaehyun

```
1. main.py
   └─ input()으로 "SET name jaehyun" 받음
   └─ split_arguments() 로 ["SET", "name", "jaehyun"] 토큰화
   └─ dispatch() 에서 SPECS["SET"] 확인 (토큰 3개 맞음)
   └─ db.cmd_set("name", "jaehyun") 호출

2. redis_db.py :: MiniRedis.cmd_set()
   └─ _sweep_expired_heap()            # 힙 top 확인, 만료된 키 있으면 선삭제
   └─ entry_size = _size_of(key, value) # utf-8 바이트 길이 계산
   └─ maxmemory 초과 여부(OOM) 체크
   └─ existing = self.table.get(key)    # ↓ hashmap.py 호출

3. hashmap.py :: HashMap.get()
   └─ index_for(key) 로 버킷 인덱스 계산  # ↓ _hash() 내부 호출
   └─ 해당 버킷 체인(hash_next)을 순회하며 key 비교
   └─ 없으면 None 리턴 → redis_db.py로 복귀

4. redis_db.py (existing이 None인 경우, 신규 키)
   └─ entry.py :: Entry(key, value) 생성   # 새 Entry 객체 생성
   └─ self.lru.insert_front(entry)         # ↓ doubly_linked_list.py 호출

5. doubly_linked_list.py :: DoublyLinkedList.insert_front()
   └─ entry.lru_next = 기존 head, head.lru_prev = entry
   └─ self.head = entry  (새 Entry가 MRU가 됨)
   └─ redis_db.py로 복귀

6. redis_db.py
   └─ self.table.put(key, entry)          # ↓ hashmap.py 호출

7. hashmap.py :: HashMap.put()
   └─ 버킷에 entry.hash_next로 체이닝 삽입
   └─ size += 1, 로드팩터 0.75 초과 시 _resize() 실행
   └─ redis_db.py로 복귀

8. redis_db.py
   └─ used_memory += entry_size
   └─ _evict_lru()   # maxmemory 설정돼 있으면 LRU 청소
   └─ "OK" 리턴 → main.py 로 복귀 → print("OK")
```

### GET name

```
1. main.py
   └─ dispatch() → db.cmd_get("name") 호출

2. redis_db.py :: MiniRedis.cmd_get()
   └─ _purge_if_expired(key)              # ↓ 만료 여부 lazy 체크
        └─ self.table.get(key)  (hashmap.py get() 재사용)
        └─ entry.expire_at 확인, 만료면 _delete_key_internal() 호출 후 삭제

   └─ entry = self.table.get(key)         # ↓ hashmap.py get() 다시 호출
        (hashmap.py 내부 동작은 SET 때와 동일: index_for → 체인 순회)

   └─ entry가 None이면 "(nil)" 바로 리턴

   └─ entry가 있으면 self.lru.move_to_front(entry)   # ↓ doubly_linked_list.py 호출

3. doubly_linked_list.py :: DoublyLinkedList.move_to_front()
   └─ entry가 이미 head면 아무것도 안 함
   └─ 아니면 entry를 현재 위치에서 떼어내고(prev/next 재연결) head 앞에 재삽입
   └─ redis_db.py로 복귀

4. redis_db.py
   └─ f'"{entry.value}"' 형태로 포맷 → main.py 로 리턴 → print('"jaehyun"')
```

**핵심 포인트**: `cmd_set`/`cmd_get` 둘 다 **hashmap.py의 get()을 재사용**하고,
LRU 갱신이 필요한 시점(신규 삽입/GET 성공/기존 키 덮어쓰기)에만 `doubly_linked_list.py`의
`insert_front`/`move_to_front`를 호출하는 구조. TTL 체크(`_purge_if_expired`)는
GET/EXISTS/DEL/EXPIRE/TTL 등 **키를 다루는 모든 명령어 진입 시점에 공통으로 먼저 실행**됨.

### DEL name

```
1. main.py
   └─ dispatch() → db.cmd_del("name") 호출

2. redis_db.py :: MiniRedis.cmd_del()
   └─ _purge_if_expired(key)
        └─ hashmap.py get() 으로 entry 조회 → 만료면 _delete_key_internal() 로 이미 삭제
        └─ 이미 만료돼서 지워진 거면 "(integer) 0" 바로 리턴 (없던 키 취급)

   └─ (안 만료됐으면) _delete_key_internal(key) 호출

3. redis_db.py :: _delete_key_internal()
   └─ hashmap.py get() 으로 entry 조회
   └─ used_memory -= 바이트 크기
   └─ self.lru.remove_node(entry)          # ↓ doubly_linked_list.py 호출
   └─ self.table.remove(key)               # ↓ hashmap.py 호출

4. doubly_linked_list.py :: remove_node()
   └─ entry가 head/tail/중간 노드인지 판별해서 prev/next 재연결, size -= 1

5. hashmap.py :: remove()
   └─ index_for(key)로 버킷 찾고 체인(hash_next) 순회하며 key 일치하는 노드 끊어냄, size -= 1

6. redis_db.py
   └─ "(integer) 1" 리턴 → main.py → print
```

### EXISTS name

```
1. main.py → dispatch() → db.cmd_exists("name")

2. redis_db.py :: cmd_exists()
   └─ _purge_if_expired(key)              # hashmap.get() 재사용, 만료면 삭제
   └─ self.table.contains(key)            # ↓ hashmap.py 호출

3. hashmap.py :: contains()
   └─ 내부적으로 get(key) 그대로 호출해서 None 여부만 판단

4. redis_db.py
   └─ 있으면 "(integer) 1", 없으면 "(integer) 0" → main.py
```

### DBSIZE

```
1. main.py → dispatch() → db.cmd_dbsize()

2. redis_db.py :: cmd_dbsize()
   └─ _sweep_expired_heap()               # ↓ min_heap.py 호출

3. min_heap.py :: peek() / pop()
   └─ heap top의 (expire_at, key)가 이미 지났으면 pop()
   └─ redis_db.py가 그 key로 hashmap.get() 해서 진짜 만료 상태인지 재확인 후 _delete_key_internal()
   └─ top이 아직 안 지났으면 while 루프 종료 (break)

4. redis_db.py
   └─ self.table.size 속성값 그대로 "(integer) N" 형태로 리턴 (hashmap.py 호출 없이 속성 직접 참조)
```

### KEYS

```
1. main.py → dispatch() → format_keys_output(db.cmd_keys())

2. redis_db.py :: cmd_keys()
   └─ _sweep_expired_heap()               # DBSIZE와 동일 (min_heap.py 호출)
   └─ self.table.keys()                   # ↓ hashmap.py 호출

3. hashmap.py :: keys()
   └─ 버킷 배열 처음부터 끝까지 순회하며 각 체인(hash_next) 따라가서 key 전부 수집

4. main.py :: format_keys_output()
   └─ 리스트를 "1) "key1"\n2) "key2"" 형식의 Redis 스타일 문자열로 변환 후 print
```

### CONFIG SET maxmemory 100

```
1. main.py
   └─ dispatch() 에서 tokens[1]=="SET", tokens[2]=="maxmemory" 형식 검증
   └─ parse_int(tokens[3]) 로 정수 파싱 (실패하면 에러 즉시 리턴, redis_db.py 호출 안 함)
   └─ db.cmd_config_set_maxmemory(100) 호출

2. redis_db.py :: cmd_config_set_maxmemory()
   └─ self.maxmemory = 100
   └─ self._evict_lru() 호출             # 바로 이 시점에 초과분 있으면 즉시 청소

3. redis_db.py :: _evict_lru()
   └─ self.lru.tail 로 LRU 노드 확인       # ↓ doubly_linked_list.py 의 tail 속성 참조
   └─ 초과하는 동안 _delete_key_internal() 반복 (위 DEL 흐름의 3~5단계와 동일)

4. redis_db.py
   └─ "OK" 리턴 → main.py
```

### INFO memory

```
1. main.py → dispatch() → db.cmd_info_memory()

2. redis_db.py :: cmd_info_memory()
   └─ 다른 자료구조 호출 없이, 이미 들고 있는 self.used_memory / self.maxmemory /
      self.evicted_keys 값 3개를 그대로 f-string으로 포맷해서 리턴
```

### EXPIRE foo 20

```
1. main.py
   └─ dispatch() 에서 parse_int(tokens[2]) 로 "20" 파싱
   └─ db.cmd_expire("foo", 20) 호출

2. redis_db.py :: cmd_expire()
   └─ _purge_if_expired(key)              # hashmap.get() 재사용
   └─ entry = self.table.get(key)         # ↓ hashmap.py 호출 (없으면 "(integer) 0")
   └─ seconds <= 0 이면 _delete_key_internal() 후 즉시 리턴

   └─ (정상 케이스) expire_at = 현재시각 + 20
   └─ entry.expire_at = expire_at         # Entry 객체 필드에 직접 기록
   └─ self.expire_heap.push((expire_at, key))   # ↓ min_heap.py 호출

3. min_heap.py :: push()
   └─ 배열 맨 끝에 추가 후 _heapify_up() 으로 부모와 비교하며 위로 이동, 최소 힙 성질 유지

4. redis_db.py
   └─ "(integer) 1" 리턴 → main.py
```

### TTL foo

```
1. main.py → dispatch() → db.cmd_ttl("foo")

2. redis_db.py :: cmd_ttl()
   └─ _purge_if_expired(key)              # hashmap.get() + 만료 시 _delete_key_internal()
   └─ entry = self.table.get(key)         # ↓ hashmap.py 호출

   └─ entry 없으면 "(integer) -2" (키 자체가 없음)
   └─ entry.expire_at 이 None 이면 "(integer) -1" (TTL 설정 안 된 키)

   └─ remaining = entry.expire_at - 현재시각
   └─ remaining <= 0 이면 _delete_key_internal() 후 "(integer) -2"
   └─ 아니면 math.ceil(remaining) 으로 올림 처리해서 "(integer) N" 리턴 → main.py
```

**공통 패턴 정리**

| 명령어 | hashmap.py 호출 | doubly_linked_list.py 호출 | min_heap.py 호출 |
|---|---|---|---|
| SET | get + put | insert_front / move_to_front | (만료 스윕 시) |
| GET | get | move_to_front | (만료 스윕 시) |
| DEL | get + remove | remove_node | - |
| EXISTS | contains(=get) | - | (만료 스윕 시) |
| DBSIZE | size 속성만 | - | peek/pop |
| KEYS | keys() | - | peek/pop |
| CONFIG SET maxmemory | (evict 시 remove) | (evict 시 remove_node) | - |
| INFO memory | - | - | - |
| EXPIRE | get | - | push |
| TTL | get | - | - |

→ **`_purge_if_expired`(지연 만료)** 와 **`_sweep_expired_heap`(능동 만료)** 이 두 개가
사실상 모든 명령어의 진입점에서 "만료된 키부터 치우고 시작"하는 공통 게이트 역할을 함.

---

## 5. 트러블슈팅

### 5-1. `ImportError: cannot import name 'DLLNode'`

- 처음엔 Entry와 별개로 DLL 노드를 감싸는 `DLLNode` 클래스를 쓰려고 했는데,
  `doubly_linked_list.py`를 Entry 자체가 노드 역할을 겸하는 구조로 단순화하면서
  `redis_db.py`의 import 문을 안 고쳐서 발생.
- **해결**: `from doubly_linked_list import DoublyLinkedList` 만 남기고,
  `entry.lru_node` 참조하던 부분들을 전부 `entry` 자체를 넘기는 방식으로 수정.

### 5-2. `hashmap.py` 내부 속성 이름 불일치

- `__init__`에서는 `self.bucket`(단수), `self.size`, `self.bucket_size`로 선언했는데
  다른 메서드들에서 `self.buckets`(복수), `self.count`, `self.capacity`를 참조 → `AttributeError`.
- **해결**: `__init__`에서 선언한 이름 기준으로 전체 통일.

### 5-3. `size()`를 메서드처럼 호출

- `self.lru.size`, `self.table.size`는 **속성(int)**인데 `self.lru.size()`처럼 괄호를 붙여서
  `TypeError: 'int' object is not callable` 발생.
- **해결**: 괄호 제거.

### 5-4. `put()`이 값 갱신을 안 함

- 같은 key로 `put()` 호출 시 주석은 "값 업데이트"라고 되어 있는데 실제로는
  `return current`만 하고 `value` 갱신 로직이 빠져있었음.
- **해결**: `current.value = entry.value` 추가.

---

## 6. 실행 로그

### 6-1. 기본 CRUD

```
mini-redis> SET name jaehyun
OK
mini-redis> GET name
"jaehyun"
mini-redis> EXISTS name
(integer) 1
mini-redis> DEL name
(integer) 1
mini-redis> GET name
(nil)
mini-redis> DBSIZE
(integer) 0
```

### 6-2. TTL 실제 만료 (EXPIRE 20초로 여유 있게 테스트)

```
mini-redis> set foo bar
OK
mini-redis> expire foo 20
(integer) 1
mini-redis> ttl foo
(integer) 16
mini-redis> get foo
"bar"
mini-redis> ttl foo
(integer) 1
mini-redis> ttl foo
(integer) -2
mini-redis> get foo
(nil)
```

- TTL이 16 → 1로 줄어드는 건 타이핑하는 사이 시간이 흐른 것.
- 완전히 만료되면 TTL은 "TTL 없음(-1)"이 아니라 **"키 없음(-2)"** 으로 바뀜 → 만료된 키는
  `_purge_if_expired()`에 의해 실제로 삭제되기 때문.

### 6-3. LRU eviction + 메모리 관리 (maxmemory=12바이트)

```
mini-redis> CONFIG SET maxmemory 12
OK
mini-redis> SET k1 v1
OK
mini-redis> SET k2 v2
OK
mini-redis> SET k3 v3
OK
mini-redis> GET k1
"v1"
mini-redis> SET k4 v4
OK
mini-redis> KEYS
1) "k3"
2) "k4"
3) "k1"
mini-redis> EXISTS k2
(integer) 0
mini-redis> INFO memory
used_memory:12
maxmemory:12
evicted_keys:1
```

- k1/k2/k3 순서로 넣고 GET k1으로 k1을 MRU로 갱신했더니, SET k4로 용량 초과됐을 때
  **LRU였던 k2가 제거**되고 k1은 살아남음 (`evicted_keys: 1`로 정확히 반영).

### 6-4. 해시맵 리사이징 (bucket_size=8, load_factor=0.75)

```python
>>> from redis_db import MiniRedis
>>> db = MiniRedis()
>>> for i in range(15):
...     print('SET key%d val%d' % (i, i), '->', db.cmd_set(f'key{i}', f'val{i}'))
...
(SET key0 ~ key14 모두 OK)
>>> print('bucket_size:', db.table.bucket_size)
bucket_size: 32
>>> print('size:', db.table.size)
size: 15
```

- 계산: 7번째 삽입(7/8=0.875 > 0.75) → 8 → 16 확장 / 13번째 삽입(13/16=0.8125 > 0.75) → 16 → 32 확장.
- 15개 넣고 최종 `bucket_size=32`, `size=15` → 이론값과 정확히 일치.

---

## 7. 자료구조 · 알고리즘 원리 심화 설명

> 이 섹션은 "동작하는 걸 보여주는 것"과는 별개로, **왜 이렇게 설계했는지 / 원리가 뭔지**를
> 직접 설명하기 위해 정리함.

### 7-1. 이중 연결 리스트가 O(1)인 이유

`doubly_linked_list.py`의 `insert_front / insert_back / remove_front / remove_back /
remove_node / move_to_front` 전부 **리스트 길이(size)와 무관하게 포인터 몇 개만 갈아끼우고 끝남.**

```python
def move_to_front(self, entry: Entry):
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
```

- **핵심은 "탐색이 없다"는 것.** 배열이었으면 중간 원소를 옮기기 위해 앞뒤 원소들을 한 칸씩
  밀어야 해서 O(n)인데, 연결 리스트는 `entry`라는 **노드 참조를 이미 들고 있는 상태**에서
  그 노드의 `prev`/`next`, 그리고 앞뒤 이웃의 `prev`/`next`만 재배선하면 끝남.
- `head`/`tail` 포인터를 따로 들고 있어서 맨 앞/뒤 삽입·삭제도 순회 없이 바로 접근 가능.
- 조건: **"이미 그 노드에 대한 참조가 있어야" O(1)이 성립함.** (임의 key로 리스트 안에서
  노드를 "찾는" 건 이 자료구조만으론 O(n) — 그래서 해시맵이 필요해짐 → 7-5 참고)

### 7-2. 해시 함수가 인덱스를 만드는 과정

```python
def _hash(self, key):
    h = 0
    for ch in key:
        h = ((h * 31) + ord(ch))
    return h

def index_for(self, key, capacity=None):
    capacity = capacity if capacity is not None else self.bucket_size
    return self._hash(key) % capacity
```

- **1단계 (`_hash`)**: 문자열을 하나의 큰 정수로 압축. 문자 하나씩 `이전값*31 + 현재문자코드`로
  누적하는 **다항 해시(polynomial hash)** 방식. 예를 들어 `"ab"`면
  `((0*31 + 'a') * 31 + 'b')` 식으로, 문자 순서와 값이 전부 결과에 반영됨.
  → 이래서 `"ab"`랑 `"ba"`가 다른 해시값이 나옴 (단순 합산이었으면 같은 값 나왔을 것).
- **2단계 (`index_for`)**: `_hash()`가 뱉는 정수는 버킷 배열 크기(8, 16, 32...)보다 훨씬 큼.
  이걸 **버킷 개수로 나눈 나머지(`%`)** 를 취해서 `[0, bucket_size)` 범위 안으로 강제로 눌러 담음
  → 이게 실제 배열 인덱스가 됨.
- **31을 곱하는 이유**: 31은 소수(prime)라서 특정 패턴의 key들이 몰려서 같은 인덱스로
  쏠리는 현상(클러스터링)이 상대적으로 적음. (Java `String.hashCode()`도 같은 방식)

### 7-3. 체이닝으로 충돌을 해결하는 방식

서로 다른 key가 `index_for()` 결과 **같은 버킷 인덱스**를 받는 걸 "충돌"이라 함.
Mini Redis는 이걸 **각 버킷을 연결 리스트로 만들어서** 해결함.

```python
def put(self, key, entry):
    idx = self.index_for(key)
    current = self.bucket[idx]
    while current is not None:
        if current.key == key:
            current.value = entry.value
            return current
        current = current.hash_next          # 같은 버킷 안에서 체인 순회

    entry.hash_next = self.bucket[idx]        # 새 entry를 체인 맨 앞에 삽입
    self.bucket[idx] = entry
```

- 버킷 하나(`self.bucket[idx]`)가 **entry들의 연결 리스트 head**를 가리키고, 각 entry는
  `hash_next`로 같은 버킷에 있는 다음 entry를 가리킴.
- 삽입은 **항상 체인 맨 앞에 붙이는 방식**이라 O(1). 조회/삭제는 체인을 순회해야 해서
  버킷 하나에 몰린 entry 개수(체인 길이)만큼 시간이 걸림 — 그래서 로드팩터 관리가 중요해짐 (7-4).

### 7-4. 로드 팩터 0.75 초과 시 버킷 2배 확장

```python
if (self.size / self.bucket_size) > self.load_factor:
    self._resize()
```

- **로드 팩터 = (저장된 개수) / (버킷 개수)**. 이 값이 커질수록 버킷 하나당 체인이 길어져서
  조회 성능이 O(1)에서 점점 O(n)에 가까워짐 (최악의 경우 모든 key가 한 버킷에 몰리는 상황).
- 0.75를 넘으면 **버킷 배열을 2배로 늘리고(`bucket_size * 2`), 기존 entry 전부를
  새 배열 크기 기준으로 다시 인덱스를 계산해서 재배치(rehash)** 함:

```python
def _resize(self):
    new_capacity = self.bucket_size * 2
    new_bucket = [None] * new_capacity
    for i in range(self.bucket_size):
        current = self.bucket[i]
        while current is not None:
            next_node = current.hash_next
            new_idx = self.index_for(current.key, new_capacity)   # capacity가 바뀌었으니 인덱스도 다시 계산
            current.hash_next = new_bucket[new_idx]
            new_bucket[new_idx] = current
            current = next_node
    self.bucket = new_bucket
    self.bucket_size = new_capacity
```

- **왜 재배치가 필요하냐면**: `index_for`가 `hash % bucket_size`라서, `bucket_size`가 바뀌면
  같은 key라도 나머지 연산 결과(인덱스)가 완전히 달라짐. 배열만 키우고 기존 entry를 그대로
  두면 엉뚱한 자리에 있는 채로 못 찾게 됨.
- resize 자체는 O(n)이지만, **2배씩 커지기 때문에 자주 일어나지 않음** (8→16→32...).
  삽입 n번 중 resize는 log₂n번 정도만 발생해서, 평균(amortized)으로 보면 삽입 1번당 여전히 O(1).

### 7-5. LRU 구현 — 해시맵과 이중 연결 리스트의 역할 분담

| 자료구조 | 역할 | 왜 필요한가 |
|---|---|---|
| 해시맵 | key로 entry를 **즉시 찾기** | DLL만 있으면 key로 노드 찾으려면 처음부터 순회(O(n)) |
| 이중 연결 리스트 | 사용 순서(MRU~LRU) **유지 + 재배치** | 해시맵만 있으면 "어떤 게 가장 오래됐는지" 알 방법이 없음 (순서 개념이 없는 자료구조라서) |

- 두 자료구조가 각자 잘하는 일만 하고, **`Entry` 객체 하나를 공유**해서 연결함
  (`entry.py`에 `hash_next`랑 `lru_prev/lru_next`가 같이 있는 이유가 이거).
- 해시맵 단독: "빠른 조회"는 되지만 "누가 제일 오래됐는지" 모름.
- DLL 단독: "순서 관리"는 되지만 특정 key의 위치를 찾으려면 head부터 순회해야 함(O(n)).
- **둘을 합쳐야만** "빠른 조회 + 빠른 순서 갱신"이 동시에 성립.

### 7-6. O(1) LRU가 실제로 성립하는 원리 (조회 + 갱신)

```python
def cmd_get(self, key):
    self._purge_if_expired(key)
    entry = self.table.get(key)      # ① 조회: 해시맵, O(1)
    if entry is None:
        return "(nil)"
    self.lru.move_to_front(entry)    # ② 갱신: DLL, O(1)
    return f'"{entry.value}"'
```

- **① 조회 단계**: `hashmap.get(key)`가 해시 계산 + 버킷 인덱싱으로 O(1)에 **entry 객체의
  메모리 참조 자체**를 반환함 (복사가 아니라 진짜 그 객체).
- **② 갱신 단계**: `move_to_front(entry)`는 방금 받은 그 참조를 그대로 넘기기 때문에,
  DLL 안에서 이 entry를 "찾을" 필요가 전혀 없음. 이미 위치를 알고 있는 노드의 포인터만
  재배선하면 끝 → O(1).
- 만약 해시맵 없이 DLL만 썼다면 ①번 단계에서 head부터 `entry.key == key`를 비교하며
  순회해야 해서 그 자체로 O(n)이 되고, 그 뒤 ②는 O(1)이어도 전체는 O(n)이 됨.
- **즉, "조회 O(1) + 갱신 O(1)"이 둘 다 성립해야 진짜 O(1) LRU** — 하나라도 O(n)이면 의미 없음.

### 7-7. TTL 관리에 최소 힙을 쓴 이유

- TTL이 걸린 key가 여러 개 있을 때, 계속 반복해서 필요한 질문은 **"지금 이 순간 만료된 게 있나?"**
  즉 **"가장 빨리 만료되는 키가 뭔가(최솟값)"** 를 빠르게 아는 것.
- 힙이 아니라 그냥 배열/리스트에 만료시각들을 저장했다면, 매번 만료 여부 확인할 때
  **전체를 훑어야(O(n))** "가장 빠른 것"을 찾을 수 있음.
- **최소 힙은 root가 항상 최솟값**이라서 `peek()`으로 O(1)에 "다음에 만료될 키"를 바로 알 수 있고,
  `push`/`pop`도 트리 높이(log n)만큼만 이동하면 돼서 O(log n).
- `redis_db.py`의 `_sweep_expired_heap()`이 이 성질을 그대로 활용:

```python
while not self.expire_heap.is_empty():
    expire_at, key = self.expire_heap.peek()   # O(1) - 최솟값(가장 빠른 만료) 확인
    if expire_at > now:
        break                                   # 제일 빠른 것도 아직 안 지났으면 나머지도 확인할 필요 없음
    self.expire_heap.pop()                      # O(log n)
    ...
```
  → root(가장 빠른 것)조차 안 지났으면 나머지는 볼 필요도 없이 바로 반복 종료 — 이게 정렬 안 된
  리스트였으면 불가능한 최적화.

### 7-8. 메모리 초과 시 Eviction 흐름 (단계별)

```
1. cmd_set() 진입
   └─ _sweep_expired_heap() 로 만료된 키 먼저 정리 (그만큼 used_memory 감소 가능)
2. 저장하려는 key/value 크기(entry_size) 계산
3. entry_size가 maxmemory 자체보다 크면 → 저장 자체를 포기하고 OOM 에러 (eviction 무의미하므로)
4. 기존 key면 값만 교체, 신규 key면 Entry 생성 + 해시맵/DLL에 삽입
5. used_memory에 entry_size 반영
6. _evict_lru() 호출
   └─ while (maxmemory 설정돼 있고) and (used_memory > maxmemory) and (리스트에 남은 게 있는 동안):
        - self.lru.tail 확인 (DLL에서 가장 오래 안 쓰인 entry = O(1) 접근)
        - 그 entry를 해시맵 + DLL 양쪽에서 제거 (_delete_key_internal)
        - used_memory 감소, evicted_keys += 1
7. used_memory가 maxmemory 이하로 떨어지는 순간 반복 종료
```

- **핵심은 "tail만 보면 된다"는 것.** LRU 후보를 찾으려고 전체를 훑을 필요 없이, DLL의 tail이
  항상 "가장 오래 안 쓰인 것"이라 O(1)로 다음 제거 대상이 바로 나옴.

### 7-9. GET 명령어 전체 흐름 (TTL 확인 → 삭제 여부 → 값 반환 → LRU 갱신 조건)

```
① TTL 확인
   _purge_if_expired(key) → hashmap.get(key)로 entry 조회
   entry.expire_at이 있고 이미 지났으면 → ② 로 바로 감

② 삭제 여부
   만료된 걸로 판정되면 _delete_key_internal() 호출
   (해시맵에서 remove + DLL에서 remove_node, used_memory도 감소)
   이 시점 이후 이 key는 "존재한 적 없는 키"처럼 취급됨

③ 값 반환
   entry = self.table.get(key) 로 다시 조회
   - None이면 (①②에서 지워졌거나 원래 없던 key) → "(nil)" 리턴, ④는 실행 안 함
   - 존재하면 entry.value를 문자열로 포맷해서 반환 준비

④ LRU 갱신 (조건부)
   entry가 존재해서 값을 반환하는 "성공 케이스에서만" self.lru.move_to_front(entry) 실행
   → nil을 반환하는 경우엔 애초에 건드릴 entry가 없으므로 LRU 갱신 자체가 발생하지 않음
   (요구사항의 "GET 성공 시에만 LRU 갱신" 규칙이 자연스럽게 지켜지는 구조)
```

### 7-10. LRU → LFU로 정책을 바꾼다면 필요한 자료구조 변경

LFU(Least Frequently Used, 최소 사용 빈도 제거)로 바꾸려면 **"얼마나 최근에 썼냐"가 아니라
"얼마나 자주 썼냐"** 를 추적해야 함. 지금 구조로는 부족한 부분:

- **Entry에 `access_count`(사용 횟수) 필드 추가** 필요 — 지금은 시간 순서만 관리하고 빈도는 안 셈.
- **DLL 하나로는 부족함.** 지금은 "전체를 하나의 순서"로만 관리하는데, LFU는
  "빈도가 같은 것들끼리 그룹"을 지어야 정확한 O(1) 구현이 가능함
  (Redis의 실제 approximate LFU도 이 방식과 유사한 근사 알고리즘 사용).
- **실전적인 O(1) LFU 설계 방향**:
  - `frequency → DoublyLinkedList` 형태로, **빈도별로 DLL을 여러 개** 둠
    (freq=1인 것들끼리 리스트, freq=2인 것들끼리 리스트...)
  - `min_freq`라는 변수를 따로 추적해서 "지금 가장 낮은 빈도가 몇인지" O(1)로 앎
  - GET/SET 발생 시: entry의 `access_count += 1` → 이전 빈도의 DLL에서 제거 →
    새 빈도의 DLL 맨 앞에 삽입 → 만약 이전 빈도 DLL이 비었고 그게 `min_freq`였다면
    `min_freq += 1`
  - eviction 시엔 `min_freq`에 해당하는 DLL의 tail만 제거하면 O(1)
- 즉, **해시맵(key→entry)은 그대로 재사용 가능**하지만, 지금의 "DLL 1개" 구조를
  **"빈도별 DLL 여러 개 + 빈도-DLL 매핑 자료구조 + min_freq 추적 변수"** 로 확장해야 함.

### 7-11. 데이터 10만 건 이상일 때 예상 병목과 개선 방안

| 병목 지점 | 원인 | 개선 방안 |
|---|---|---|
| 해시맵 resize 순간 지연 | `bucket_size=8`에서 시작 → 10만 건까지 가려면 resize가 약 14번(log₂(100000/8)) 발생, 매번 O(n) 전체 재배치 | 초기 용량을 예상 규모에 맞게 크게 잡거나(사전 용량 예약), Redis처럼 **점진적 리해싱(incremental rehashing)** 으로 한 번에 몰아서 하지 않고 여러 명령어에 걸쳐 나눠 처리 |
| `KEYS` 명령어 | 버킷 전체(`bucket_size`) + 체인을 전부 순회하는 O(n) 연산 | 실제 Redis도 `KEYS *`는 프로덕션 비권장 — 커서 기반 `SCAN`처럼 한 번에 일부만 순회하는 방식으로 교체 |
| `_sweep_expired_heap` 호출 빈도 | 거의 모든 명령어 진입 시 호출되는데, TTL 걸린 키가 많아지면 힙 크기도 커짐 | 매 명령어마다 하지 않고 별도 백그라운드 주기(예: N번 명령어마다 1번, 혹은 별도 스레드)로 분리 |
| 체인 길이 불균형 | 해시 함수(다항 해시, 31 곱셈) 자체 품질 문제로 특정 key 패턴에서 충돌이 몰릴 가능성 | 실측 체인 길이 분포 모니터링 후, 필요하면 FNV-1a나 MurmurHash 같은 더 검증된 해시 함수로 교체 |
| 메모리 실측치와 `used_memory` 괴리 | 지금 계산식은 key/value 바이트만 더하고 파이썬 객체 자체 오버헤드는 무시 | → 7-12에서 별도 정리 |

### 7-12. `used_memory`에 자료구조 오버헤드를 반영하는 보정 방안

현재 계산식:
```python
used_memory = Σ(len(utf8(key)) + len(utf8(value)))
```
이건 **문자열 데이터만** 계산하고, 실제로 메모리를 차지하는 다음 요소들은 전부 빠져 있음:
- `Entry` 객체 자체의 필드들(`expire_at`, `lru_prev`, `lru_next`, `hash_next` — 포인터 4~5개)
- 해시맵 버킷 배열(`self.bucket`)의 슬롯 자체가 차지하는 공간
- 힙(`expire_heap.data`)에 쌓인 `(expire_at, key)` 튜플들

**보정 방안 두 가지**

1. **고정 오버헤드 상수 방식 (간단, 근사치)**
   ```python
   ENTRY_OVERHEAD = 40  # 포인터 필드들에 대한 대략적인 고정 바이트 수 (경험적 추정)
   used_memory = Σ(len(utf8(key)) + len(utf8(value)) + ENTRY_OVERHEAD)
   ```
   - 구현은 제일 쉬운데, 실제 파이썬 객체 크기와는 오차가 있을 수 있음 (근사치일 뿐).

2. **`sys.getsizeof()` 활용 방식 (더 정밀)**
   ```python
   import sys
   entry_overhead = sys.getsizeof(entry)  # Entry 객체 자체의 실측 크기
   ```
   - key/value 문자열 자체의 크기도 `sys.getsizeof()`로 재는 게 `len().encode()`보다 정확
     (파이썬 문자열 객체 자체에도 헤더 오버헤드가 있음).
   - 다만 이것도 참조하는 다른 객체(다른 곳에서도 쓰이는 문자열 등)까지 깊게 재는 건 아니라서
     **완전히 정확한 프로세스 메모리량은 아니고 여전히 근사치**.

- 추가로, 해시맵 버킷 배열 크기(`bucket_size * 포인터크기`)나 힙 배열 크기처럼
  **개별 entry가 아니라 구조 전체에 걸린 고정 비용**은 `used_memory`와 별도로
  `INFO memory`에 `struct_overhead` 같은 필드를 추가해서 따로 보여주는 것도 방법.