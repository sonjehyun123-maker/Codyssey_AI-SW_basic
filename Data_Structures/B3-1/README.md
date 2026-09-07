# Mini Redis

`dict`, `set`, `collections` 등 파이썬 내장 자료구조를 전혀 사용하지 않고, 해시맵·이중 연결 리스트·최소 힙을 배열 기반으로 직접 구현해서 **LRU 캐시 + TTL 만료가 동작하는 Redis 서브셋**을 만든 CLI 프로젝트입니다.

---

## 1. Overview

SET/GET/DEL 같은 기본 명령어부터 `CONFIG SET maxmemory`, `EXPIRE`/`TTL`까지 지원하는 Redis 스타일 REPL입니다. 겉으로는 Redis 명령어를 흉내 내지만, 목적은 **"왜 Redis가 빠른가"를 자료구조 레벨에서 증명하는 것**이었습니다.

```
mini-redis> SET name jaehyun
OK
mini-redis> GET name
"jaehyun"
mini-redis> EXPIRE name 20
(integer) 1
mini-redis> TTL name
(integer) 16
```

## 2. Problem

캐시 시스템이 실무에서 반드시 마주치는 세 가지 문제를 자료구조로 직접 풀어야 했습니다.

- **빠른 key-value 조회**를 어떻게 O(1)에 가깝게 만들 것인가 (해시맵)
- **메모리가 찰 때 무엇을 지울지**를 어떻게 O(1)에 판단할 것인가 (LRU)
- **키가 자동으로 만료**되는 걸 어떻게 매번 전체를 훑지 않고 처리할 것인가 (TTL / 최소 힙)

그리고 이 세 가지를 각각 따로 만드는 게 아니라 **하나의 엔진 안에서 서로 맞물려 동작**하게 만드는 것이 핵심 과제였습니다.

## 3. Architecture

자료구조별로 파일을 완전히 분리하고, `redis_db.py`가 이들을 조립하는 구조입니다.

```
entry.py                # 공유 데이터 모델 (해시맵/LRU가 같이 참조하는 노드)
doubly_linked_list.py   # 이중 연결 리스트 — LRU 순서 관리
hashmap.py              # 해시맵 — 체이닝 방식 충돌 처리
min_heap.py             # 최소 힙 — TTL 만료 관리
redis_db.py             # 위 세 자료구조를 조립하는 MiniRedis 엔진
main.py                 # REPL / 명령어 파싱 / 출력 포맷
```

**SET 명령어 하나의 실행 흐름**만 봐도 세 자료구조가 어떻게 맞물리는지 드러납니다.

```
main.py (파싱)
  → redis_db.py :: cmd_set()
      → hashmap.py :: get()       기존 키인지 확인
      → entry.py :: Entry()       신규 키면 노드 생성
      → doubly_linked_list.py :: insert_front()   MRU로 등록
      → hashmap.py :: put()       해시맵에 삽입 (로드팩터 초과 시 resize)
      → redis_db.py :: _evict_lru()   maxmemory 초과 시 LRU부터 삭제
```

## 4. Core Concepts

| 개념 | 적용 위치 | 핵심 |
|---|---|---|
| 해시맵 + 체이닝 | `hashmap.py` | 다항 해시(`h*31+ord(ch)`)로 인덱스 계산, 충돌은 연결 리스트로 체이닝 |
| 로드 팩터 / 리해싱 | `hashmap.py` | 0.75 초과 시 버킷 2배 확장 + 전체 재배치, amortized O(1) 유지 |
| 이중 연결 리스트 | `doubly_linked_list.py` | `head`=MRU, `tail`=LRU. 포인터 재배선만으로 O(1) 순서 갱신 |
| 최소 힙 | `min_heap.py` | `(expire_at, key)`를 push, root가 항상 가장 빨리 만료되는 키 |
| Lazy + Active 만료 | `redis_db.py` | 명령어 진입 시 `_purge_if_expired`(지연), 별도 시점에 `_sweep_expired_heap`(능동) |

가장 중요한 설계는 **`Entry` 객체 하나가 해시맵의 체이닝 포인터(`hash_next`)와 LRU의 이중 연결 포인터(`lru_prev/lru_next`)를 동시에 들고 있다**는 점입니다. 이 덕분에 해시맵에서 O(1)에 찾은 객체 참조를 그대로 LRU 리스트에 넘겨서, "찾기"와 "순서 갱신"이 각각 O(1)로 분리된 채 하나의 파이프라인으로 이어집니다.

## 5. Implementation

**해시맵 충돌 처리 (체이닝)**
```python
def put(self, key, entry):
    idx = self.index_for(key)
    current = self.bucket[idx]
    while current is not None:
        if current.key == key:
            current.value = entry.value
            return current
        current = current.hash_next
    entry.hash_next = self.bucket[idx]
    self.bucket[idx] = entry
    self.size += 1
    if (self.size / self.bucket_size) > self.load_factor:
        self._resize()
```

**LRU 갱신 — 탐색 없이 포인터만 재배선**
```python
def move_to_front(self, entry):
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

**TTL 능동 정리 — 힙 root만 확인**
```python
while not self.expire_heap.is_empty():
    expire_at, key = self.expire_heap.peek()
    if expire_at > now:
        break
    self.expire_heap.pop()
    ...
```

## 6. Design Decisions

**왜 해시맵 + 이중 연결 리스트를 같이 썼는가?**
해시맵만 있으면 "가장 오래 안 쓰인 키"를 알 방법이 없고(순서 개념 부재), DLL만 있으면 특정 key를 찾으려면 순회(O(n))가 필요합니다. 두 자료구조가 서로의 약점을 메꿔서 "빠른 조회 O(1) + 빠른 순서 갱신 O(1)"이 동시에 성립합니다.

**왜 TTL 관리에 최소 힙을 썼는가?**
배열에 만료 시각을 그냥 저장하면 "지금 만료된 게 있나?"를 확인할 때마다 전체를 훑어야(O(n)) 합니다. 최소 힙은 root가 항상 최솟값이라 `peek()` O(1)로 "다음에 만료될 키"를 즉시 알 수 있고, push/pop도 O(log n)에 끝납니다.

**왜 로드 팩터 0.75인가?**
저장 개수/버킷 개수 비율이 커질수록 체인이 길어져 조회가 O(1)에서 O(n)에 가까워집니다. 0.75를 넘으면 버킷을 2배로 늘려 재배치하는데, 2배씩 커지므로 resize는 삽입 n번 중 log₂n번만 발생해 amortized O(1)을 유지합니다.

## 7. Testing

정식 유닛 테스트 프레임워크 대신 REPL 실행 로그로 각 시나리오를 직접 검증했습니다.

| 시나리오 | 검증 내용 | 결과 |
|---|---|---|
| 기본 CRUD | SET/GET/EXISTS/DEL/DBSIZE | 정상 동작 |
| TTL 만료 | EXPIRE 후 시간 경과 시 TTL -1(미설정)이 아닌 -2(키 없음)로 전환 | `_purge_if_expired`로 실제 삭제됨 확인 |
| LRU eviction | `maxmemory=12`, 4개 키 삽입 + GET으로 갱신 | 갱신 안 된 키(`k2`)가 정확히 evict, `evicted_keys` 카운트 일치 |
| 해시맵 리사이징 | 15개 키 삽입 (`bucket_size=8`, `load_factor=0.75`) | 7번째·13번째 삽입에서 각각 resize 발생, 최종 `bucket_size=32` 이론값과 일치 |

## 8. Result

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

k1/k2/k3 순으로 삽입 후 GET k1으로 MRU 갱신 → SET k4로 용량 초과 시 **LRU였던 k2만 정확히 제거**되고 k1은 살아남는 것을 확인했습니다.

## 9. What I Learned

- "O(1)"이라는 말은 자료구조 하나만으로는 잘 성립하지 않는다는 것. LRU가 진짜 O(1)이려면 **조회(해시맵)와 갱신(DLL)이 둘 다** O(1)이어야 하고, 하나라도 O(n)이면 전체가 O(n)이 됩니다.
- 리사이징·로드 팩터처럼 "가끔 비싼 연산"을 **amortized 관점**으로 설계하는 법.
- Lazy 만료(조회 시점에 확인)와 Active 만료(별도로 미리 정리)를 함께 둬야 하는 이유 — 하나만으로는 메모리가 남거나(Lazy만) 오버헤드가 커지는(Active만) 트레이드오프가 생깁니다.
- 디버깅 과정에서 속성명 불일치(`self.bucket` vs `self.buckets`), `size`를 메서드처럼 호출하는 실수 등 기본적인 실수들이 실제로 어디서 잘 발생하는지 체감했습니다.

## 10. Future Improvements

- **LFU 정책 전환**: 현재 구조에 `access_count` 필드와 "빈도별 DLL + `min_freq` 추적"을 추가하면 O(1) LFU로 확장 가능
- **대용량 대응**: 데이터 10만 건 이상 시 예상되는 병목(해시맵 리사이즈 지연, `KEYS` 전체 스캔)에 대해 점진적 리해싱, `SCAN` 방식, 샤딩 등의 개선 방향 검토
- **메모리 계산 정교화**: 현재 `used_memory`는 문자열 바이트만 계산 — `Entry` 객체 오버헤드(포인터 4~5개)를 반영한 보정 상수 추가
- 정식 유닛 테스트(pytest) 도입 및 GitHub Actions 연동