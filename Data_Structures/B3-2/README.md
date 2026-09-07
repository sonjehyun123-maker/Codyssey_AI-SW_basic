# Mini Git

Git의 내부 구조 — 커밋 그래프(DAG), 콘텐츠 주소화 해시, 위상 정렬, BFS 최단 경로, 역색인 — 을 그래프 라이브러리나 `sorted()` 없이 직접 구현한 CLI 기반 Mini Git입니다.

---

## 1. Overview

Git을 "사용"하는 게 아니라 Git이 **내부적으로 어떻게 동작하는지**를 구현하며 이해하기 위한 프로젝트입니다. `INIT`/`BRANCH`/`COMMIT` 같은 기본 명령어부터, 커밋 그래프를 위상 정렬로 출력하는 `LOG`, 두 커밋 사이 최단 경로를 찾는 `PATH`, 키워드/작성자로 커밋을 검색하는 `SEARCH`까지 지원합니다.

```
> init jaehyun
> commit "first commit"
> branch feature
> switch feature
> commit "add feature"
> log
commit 3f9a1c... (HEAD -> feature)
Author: jaehyun
Date:   2026-01-01 12:00:00

    add feature

commit 8b2e40... (main)
Author: jaehyun
Date:   2026-01-01 11:00:00

    first commit
```

## 2. Problem

Git을 매일 쓰지만 "커밋 hash는 왜 저렇게 생겼는지", "`git log`는 왜 항상 부모가 자식보다 먼저 나오는지", "짧은 hash 7자리만 써도 왜 대부분 안 겹치는지" 같은 질문에 답하려면 Git 내부의 자료구조를 직접 만들어봐야 했습니다. 핵심 과제는 다음 세 가지였습니다.

- 커밋을 **내용 자체로 식별**하려면 어떤 해시가 필요한가 (Content-Addressable Storage)
- 부모-자식 관계로 얽힌 커밋들을 **일관된 순서**로 출력하려면 어떤 그래프 순회가 필요한가 (위상 정렬)
- 두 커밋 사이 **최단 경로**, 그리고 **키워드로 검색**은 어떤 자료구조로 O(1)에 가깝게 만들 수 있는가

## 3. Architecture

```
entry.py        # Commit 클래스 — message/author/parents/timestamp/hash(40자리)
hashmap.py       # Node(체이닝 래퍼) + HashMap — hash 앞 2자리를 버킷 번호로 직접 사용
Repository.py    # 저장소 상태 — branches, head, current_user (INIT/BRANCH/SWITCH/COMMIT)
graph.py         # DAG 탐색 — log(위상 정렬), ancestors(BFS), path(BFS 최단 경로)
git_index.py     # InvertedIndex — keyword/author 역색인
sort.py          # 병합 정렬 (sorted() 사용 금지 제약)
main.py          # REPL, 명령어 파싱, short_hash/resolve_hash(40자리↔4자리 변환)
```

**COMMIT 실행 흐름**

```
main.py (파싱)
  → Repository.py :: commit()
      → entry.py :: Commit()          message+author+parents+timestamp → SHA-1 → 40자리 hash
      → hashmap.py :: put()           hash 앞 2자리로 버킷 인덱싱, 체이닝 삽입
      → git_index.py :: add_commit()  keyword/author 역색인 즉시 갱신
      → 현재 브랜치의 tip을 새 커밋으로 갱신
```

## 4. Core Concepts

| 개념 | 적용 위치 | 핵심 |
|---|---|---|
| SHA-1 해시 | `entry.py` | `message+author+parents+timestamp` → 40자리 hash. 카운터 방식 대신 SHA-1을 택해 Content-Addressable Storage를 직접 체감 |
| 해시맵 버킷 샤딩 | `hashmap.py` | hash 앞 2자리를 그대로 버킷 번호로 사용(256버킷) — 실제 Git의 `.git/objects/xx/` 디렉토리 샤딩과 동일한 발상 |
| 위상 정렬(DFS) | `graph.py :: log()` | 부모를 먼저 방문하는 post-order DFS로 "부모가 자식보다 먼저" 조건 만족, 브랜치별 그룹핑 |
| BFS 최단 경로 | `graph.py :: path()` | parents(단방향)를 일회용 양방향 그래프로 변환해 무방향 최단 경로 계산 |
| 병합 정렬 | `sort.py` | `sorted()` 금지 제약 + 안정 정렬 필요(`--sort-by=author`에서 동일 작성자 순서 유지)로 직접 구현 |
| 역색인 | `git_index.py` | keyword/author → commit hash 리스트. COMMIT 시점에 즉시 갱신되어 SEARCH가 전체 순회 없이 조회 |

가장 중요한 설계는 **저장은 항상 40자리, 표시는 명령어마다 다르다**는 원칙입니다. `LOG`/`ANCESTORS`는 실제 `git log` 기본형처럼 40자리 전체를, `COMMIT` 확인 메시지·`PATH`·`SEARCH`는 짧은 4자리를 보여줍니다. 사용자가 어느 길이로 입력하든 `resolve_hash()`가 저장된 40자리 중 그 접두사와 일치하는 커밋을 찾아 되돌립니다.

## 5. Implementation

**해시맵 버킷 인덱싱 — 접두사를 직접 버킷 번호로**
```python
def _hash_index(self, key):
    return int(key[:2], 16)
```
SHA-1 출력은 이미 균등 분포하도록 설계돼 있어, 별도 믹싱 함수(djb2 등) 없이 앞 2자리를 그대로 버킷 번호(256개)로 써도 충돌이 고르게 분산됩니다.

**위상 정렬 LOG — 리프에서 시작해 브랜치별로 그룹핑**
```
1. 리프(다른 커밋의 parent로 참조되지 않는 커밋 = 각 브랜치 tip) 탐색
2. 리프들을 생성 시간순 정렬 (sort.py 재사용)
3. 각 리프에서 부모 우선 post-order DFS로 조상 전체를 통째로 끌어옴
   → 한 브랜치의 커밋들이 결과 안에서 흩어지지 않고 연속으로 묶임
```

**BFS 최단 경로 — 일회용 양방향 그래프**
```
Commit.parents는 자식→부모 단방향만 저장 (부모 생성 시점엔 자식이 존재하지 않아 역방향 저장이 원천 불가능)
→ PATH 계산 시에만 build_undirected_graph()로 부모→자식 방향까지 추가한 사본을 만들어 사용
→ 원본 parents는 건드리지 않아 LOG/ANCESTORS의 방향성은 그대로 유지
```

## 6. Design Decisions

**왜 카운터 대신 SHA-1인가?**
카운터 기반은 구조적으로 충돌이 불가능해 더 단순하지만, Git이 분산 환경(중앙 서버 없이 여러 개발자가 독립적으로 커밋 생성)이라는 전제를 체감하려면 "내용이 곧 주소"인 Content-Addressable Storage를 직접 구현해봐야 한다고 판단했습니다.

**왜 djb2 대신 hash 앞 2자리를 버킷 번호로 썼는가?**
Mini Redis에서는 임의의 문자열 key를 다루기 때문에 djb2 같은 믹싱 함수가 필요했지만, Mini Git의 key는 이미 SHA-1이 만든 균등분포 값이라 추가로 섞는 연산이 불필요한 중복이었습니다. 이 판단은 트러블슈팅 과정에서 얻은 것으로(7-3절), 처음엔 Mini Redis 코드를 그대로 재사용했다가 이후 교체했습니다.

**왜 저장은 40자리, 조회는 4자리로 분리했는가?**
처음엔 저장 자체를 4자리로 줄이고 충돌 시 자릿수를 늘리는 `extend_hash()` 방식을 시도했지만(7-2절, 이후 폐기), 실제 Git이 "저장은 항상 40자리, 표시만 짧게" 하는 방식과 근본적으로 다르다는 결론에 도달해 현재 구조로 전면 재설계했습니다.

**왜 LOG에서 형제 브랜치 순서를 리프 기준으로 정했는가?**
처음엔 전체 커밋을 날짜로 tie-break하는 방식을 시도했지만(7-6절, 이후 폐기), 이 시스템에서는 "부모의 timestamp가 항상 자식보다 이르다"는 인과관계가 구조적으로 성립하기 때문에, 날짜 정렬만으로도 위상정렬 조건이 저절로 만족되어 `--sort-by=date`와 결과가 완전히 중복되는 문제를 발견했습니다. 그래서 브랜치 tip(리프)만 날짜순으로 정렬하고 각 리프에서 조상을 통째로 끌어오는 방식으로 바꿔, 브랜치 줄기가 서로 안 섞이게 만들었습니다.

## 7. Testing

정식 유닛 테스트 대신 `etc/demo_script`로 전체 명령어(INIT/COMMIT/BRANCH/SWITCH/LOG/SEARCH/PATH/ANCESTORS)를 순차 실행하며 정상 케이스와 에러 케이스를 함께 검증했습니다.

| 시나리오 | 검증 내용 |
|---|---|
| INIT 재호출 | 이미 초기화된 저장소에서 다시 INIT해도 branches/head가 보존되고 current_user만 갱신 (7-4절, "유령 커밋" 버그 수정 확인) |
| BRANCH 이름 중복 | 기존 브랜치 이름으로 재생성 시도 시 `Branch already exists`로 거부 (7-5절, "몰래 덮어쓰기" 버그 수정 확인) |
| 짧은 hash 조회 | 매칭 0개 → `Unknown commit`, 매칭 2개 이상 → `Ambiguous commit`, 매칭 1개 → 정상 확정 |
| LOG 브랜치 그룹핑 | 여러 브랜치가 있을 때 한 브랜치의 커밋들이 결과 안에서 연속으로 묶여 나오는지 확인 |

## 8. Result

```
> init jaehyun
> commit "first commit"
> branch feature
> switch feature
> commit "add feature"
> log
commit 3f9a1c2b8e7d6a5f4c3b2a1e0d9c8b7a6f5e4d3c (HEAD -> feature)
Author: jaehyun
Date:   2026-01-01 12:00:00

    add feature

commit 8b2e40f1a9c8d7e6b5a4f3e2d1c0b9a8f7e6d5c4 (main)
Author: jaehyun
Date:   2026-01-01 11:00:00

    first commit

> search --author=jaehyun
Found 2 commits by jaehyun
```

리프(브랜치 tip)에서 시작해 조상을 통째로 끌어오는 방식 덕분에, `feature` 브랜치의 커밋이 `main`보다 먼저 나오면서도 서로 섞이지 않고 각자 묶여서 출력되는 것을 확인했습니다.

## 9. What I Learned

- "짧은 hash로도 대부분 안 겹친다"는 게 우연이 아니라, **저장은 항상 40자리 유지 + 조회만 접두사 매칭**이라는 명확한 설계 원칙 위에서 성립한다는 것.
- 같은 해시맵이라도 **key의 통계적 성질(임의 문자열 vs 이미 균등분포된 SHA-1)에 따라 필요한 해시 함수가 달라진다**는 것 — Mini Redis의 djb2를 그대로 재사용했다가 불필요한 연산임을 깨닫고 교체한 과정에서 체감했습니다.
- 그래프에서 "정렬 기준을 하나 바꾸면 다른 정렬 기준과 결과가 완전히 중복될 수 있다"는 것 — 날짜 tie-break가 `--sort-by=date`와 사실상 같아진 사례에서 확인했습니다.
- 단방향 참조(자식→부모)만 있는 자료구조에서 양방향 탐색이 필요할 때, **원본을 건드리지 않고 일회용 사본을 만드는 패턴**의 필요성.

## 10. Future Improvements

- 해시맵 리해싱 미구현 — 현재 256버킷 고정, load factor 0.75 기준 커밋 200개 근접 시 이론상 리해시 필요 (실제 Git은 이 규모에서 packfile 전략으로 전환)
- `merge` 명령어 및 diff 기능 (현재 보너스 과제로 범위 제외)
- 결정론적 테스트 어려움 — timestamp가 hash 계산에 포함돼 동일 입력도 매번 다른 hash가 나와, 현재는 REPL 시나리오로 구조적 성질만 확인 중. Mocking 등으로 시간 고정 후 pytest 도입 검토
- 정렬 알고리즘 성능 비교 (보너스 과제, 미구현)