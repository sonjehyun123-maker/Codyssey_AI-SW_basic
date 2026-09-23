# B5-1 도서 대여 DB — 개념 학습 노트

평가 피드백을 바탕으로 진행한 개념 학습 세션 정리.  
각 항목은 내가 직접 이해하고 설명한 내용을 기준으로 작성.

---

## 1. 정규화 vs 비정규화

정규화는 데이터의 중복을 줄이기 위해 그것을 참조되는 형태로 바꾼 것이고, 이 경우 join이나 데이터를 찾는 데 한 단계를 더 거쳐야 할 수 있다.

비정규화는 데이터의 중복을 의도적으로 허용해 쿼리 속도를 높이지만, 데이터 관리(수정/삽입/삭제)에 어려움이 있을 수 있다.

그래서 서로 어떤 방식으로 할지, 데이터 구조와 테이블 구조를 보고 잘 생각해봐야 한다. 특히 "삽입 → 출력"만 하는 데이터(로그성 데이터)에만 비정규화를 쓰고, 나머지는 정규화를 지향하는 쪽이 좋다.

---

## 2. 정규형 (1NF / 2NF / 3NF / BCNF)

- **1NF**: 한 칸에 하나의 원자값만 들어가야 함 (반복 그룹 금지)
- **2NF**: 1NF에서, PK 일부에만 종속되는 컬럼(부분 함수 종속)을 분리해 완전 함수 종속으로 만드는 것
- **3NF**: 2NF에서, 컬럼끼리 이중으로 종속되는(이행적 함수 종속) 데이터를 쪼개 더 구체화하는 것
- **BCNF**: 3NF가 업그레이드된 개념으로, 결정할 수 있는 값(결정자)은 무조건 키의 자격을 가져야 한다는 것

---

## 3. N:M 관계 — book_author 브릿지 테이블

`book.author_id`는 삭제해야 한다.

하나의 책은 여러 작가를 가질 수 있고(공저), 하나의 작가도 여러 책을 가질 수 있기 때문에(N:M) `book_author` 브릿지 테이블로 관계를 따로 관리해야 하며, 진실이 두 군데(book.author_id와 book_author)에 있으면 갱신 이상이 다시 생긴다.

## book_author 브릿지 테이블 도입 — 전/후 비교

### Before — book.author_id (1:N 가정)

```sql
CREATE TABLE book (
    book_id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title           TEXT NOT NULL,
    ...
    author_id       INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES author(author_id)
);
```

- "책 1권 = 저자 1명"만 표현 가능
- 공저 도서를 넣으려면 `author_id` 컬럼에 값을 하나만 넣을 수 있어서, 나머지 저자는 저장할 곳이 없음

### After — book_author 브릿지 테이블 (N:M)

```sql
-- book에서 author_id 제거
CREATE TABLE book (
    book_id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title           TEXT NOT NULL,
    ...
    -- author_id 컬럼 삭제됨
);

-- 관계를 별도 테이블로 분리
CREATE TABLE book_author (
    book_id     INTEGER NOT NULL,
    author_id   INTEGER NOT NULL,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    FOREIGN KEY (author_id) REFERENCES author(author_id)
);
```

- 책 1권에 저자 여러 명(공저), 저자 1명이 여러 책 — 양방향 N 모두 표현 가능
- "관계를 표현하는 곳"이 `book_author` 한 곳으로 통일됨 (Before는 `book.author_id`가 유일한 진실이었다면, After는 `book_author`가 유일한 진실)

### 검증

공저 예시 도서를 넣고 실제로 조회해 확인함:

```sql
SELECT b.title, a.author_name
FROM book b
JOIN book_author ba ON b.book_id = ba.book_id
JOIN author a ON ba.author_id = a.author_id
WHERE b.book_id = 19;
```

```
            title             | author_name
------------------------------+-------------
 사피엔스 그 이후 (공저 예시) | 유발 하라리
 사피엔스 그 이후 (공저 예시) | 유시민
(2 rows)
```

### 왜 바꿨나

- Before 구조로는 이 공저 도서를 아예 저장할 수 없었음 (author_id는 값 하나만 허용)
- 지금은 요구사항(최소 4테이블, 1:N 2개 이상)을 이미 충족한 상태였지만, "실제 도메인(도서관)은 N:M이 현실"이라는 점을 반영해 정규화 근거를 더 명확히 하기 위해 도입함



---

## 4. 조인 읽는 순서 (Q6 기준)

대여 테이블에서,

1. 대여의 `member_id`와 `member` 테이블의 `member_id`가 같은 것을 찾고
2. 대여의 `book_id`와 `book` 테이블의 `book_id`가 같은 것을 찾아
3. 최종적으로 `rental_id / member_name / title / rental_date / due_date`를 출력하고
4. `rental_id` 순으로 정렬한다.

→ 읽는 순서는 **FROM부터, JOIN 나온 순서대로.**

---

## 5. 서브쿼리 읽는 순서 (Q12 기준)

`rental`에서 `book_id`를 가져오고(이 결과를 A라 하면), `book` 테이블에서 A에 없는 것만 골라내어 최종적으로 `title`만 출력한다.

→ 안쪽 서브쿼리가 먼저 실행되고, 바깥쪽이 그 결과를 재료로 씀.

---

## 6. CHECK 제약조건

CHECK은 DB에 데이터가 들어갈 때 걸리는 최소한의 제한이다.

예: 나이 같은 값은 0 이하가 될 수 없고, 대여 날짜는 반납 만료 날짜보다 뒤일 수 없다는 규칙을 강제한다.

애플리케이션 코드와 무관하게 DB 엔진 레벨에서 최후의 방어선으로 동작함(직접 psql로 INSERT 쳐도 막히는 걸 실습으로 확인).

---

## 7. 트랜잭션 원자성

트랜잭션 중간에 CHECK 위반 등으로 하나라도 실패하면, 이미 성공했던 이전 INSERT까지 전부 롤백된다(전부 성공 아니면 전부 실패).

실습으로 3개 INSERT 중 2번째가 실패했을 때 테이블이 0행으로 비어있는 것을 확인함.

---

## 8. VACUUM vs VACUUM FULL

실무에서는 데이터를 지울 때 바로 지우지 않는다.

빈 공간을 처리하는 데 비용이 들기 때문에, 죽은 데이터 처리를 해두고 분기(트랜잭션 가시성 조건) 또는 일정 크기마다(용량 임계치) 정리한다.

- **일반 VACUUM(autovacuum)**: 동시성 때문에 자동/자주 실행, line pointer만 재사용 가능 상태로 바꿈(파일 크기 안 줄어듦)
- **VACUUM FULL**: 테이블 전체 락 걸고 재작성, 실제로 공간 반환, 비용이 커서 수동/드물게 실행

---

## 9. DB 선택 기준 (관계형 vs 비관계형)

관계 자체가 DB 테이블을 가장 잘 표현하는 단어다.

책과 작가의 관계, 책과 사용자가 빌리는 관계처럼 "연결되어 있다"는 사실 자체가 중요한 데이터라면, Key-Value(Redis)나 사용자마다 다르게 바뀌는 Document형(MongoDB)보다 관계형(SQL)이 낫다.

---

## 10. 인덱싱 — 배열 vs 해시 vs 트리(B+tree)

DB가 배열 대신 트리 인덱스를 쓰는 이유는, 데이터가 삽입/제거/변경될 때마다 정렬된 자리를 유지하는 비용이 크기 때문이다(배열은 중간 삽입 시 뒤 원소를 다 밀어야 함).

자료구조(큐/스택/트리/해시맵 등) 중에서, 수억 개의 데이터를 저장하는 DB 입장에서 조회·저장·삽입·삭제를 모두 빠르게 하기 위해 트리를 선택했고, 트리 중에서도 같은 레벨에 데이터를 최대한 많이 넣을 수 있는(레벨당 fanout이 큰) B+tree를 사용해 DB의 핵심 역할(삽입/삭제/조회/변경)을 빠르게 한다.

> (+ B+tree는 삽입/삭제마다 스스로 균형을 맞춰서, 일반 BST처럼 한쪽으로 치우쳐 O(n)까지 나빠지는 걸 방지하고 항상 O(log n)을 보장한다.)

---

# 남은 학습 항목

- [ ] 인덱싱을 컴퓨터과학 전반(직접 주소 계산 / 해시 / 비교 기반)으로 넓혀서 정리 — 진행 중
- [ ] 주석 없이 조인/서브쿼리 쿼리를 바로 읽는 실전 연습 — 계속 필요

---

# 개념 보완 노트

## 1. DB와 엑셀의 차이

| | 엑셀 | 관계형 DB |
|---|---|---|
| 관계 표현 | 시트 간 연결 없음, 수동 VLOOKUP | FK로 테이블 간 관계를 강제 |
| 무결성 | 아무 값이나 입력 가능 | PK/FK/CHECK로 잘못된 값 자체를 차단 |
| 동시성 | 동시 편집 시 충돌/덮어쓰기 위험 | 트랜잭션으로 동시 접근을 안전하게 관리 |
| 검색/집계 | 수식으로 직접 계산 | SQL로 대량 데이터도 빠르게 질의 |

**핵심:** 엑셀은 "데이터를 보여주는 표"고, DB는 "데이터 간 관계와 규칙을 강제하는 시스템"이다.

---

## 2. PK와 FK의 역할

- **PK (Primary Key)** — 그 행의 "신원증명". 테이블 안에서 유일해야 하고 절대 중복/NULL 불가.
  - 예: `book.book_id` — 세상에 같은 제목의 책이 여러 권 있어도, `book_id`는 무조건 하나만 존재

- **FK (Foreign Key)** — 다른 테이블의 PK를 "참조"하는 값. 그 값이 실제로 존재하는지 DB가 검증해줌.
  - 예: `rental.book_id`는 `book.book_id`를 참조 → 존재하지 않는 `book_id`로 대여 기록을 넣으려 하면 DB가 거부함

즉 **PK = "나는 누구다"**, **FK = "나는 저것과 연결되어 있다"**.

---

## 3. 테이블을 왜 나눴는가

만약 `rental` 테이블 하나에 회원명, 책 제목, 카테고리명, 저자명을 다 때려박았다면:

- 같은 책이 100번 대여되면 책 제목·카테고리·저자 정보가 100번 중복 저장됨
- 책 제목에 오타가 있어서 고치려면 100개 행을 다 고쳐야 함 (수정 이상)
- 이래서 "책 정보는 `book`에 한 번만, `rental`은 `book_id`만 참조"하도록 분리함

**분리 기준:** "이 정보가 독립적으로 존재할 수 있는가?" → 책은 대여 기록이 없어도 존재할 수 있으니 별도 테이블.

---

## 4. 컬럼 타입 선정 이유

- `TEXT` vs `VARCHAR(n)` — PostgreSQL에서는 둘의 성능 차이가 없어서 길이 제한이 꼭 필요한 게 아니면 `TEXT`를 씀 (다른 DB, 예: MySQL은 다를 수 있음)
- `DATE` vs `TIMESTAMP` — 대여일/반납일은 "몇 시 몇 분"까지 필요 없고 "그 날짜"만 중요해서 `DATE`로 충분
- `BOOLEAN` (`is_available`) — 상태값이 참/거짓 두 가지뿐이라 `INTEGER`(1/0)보다 의미가 명확한 `BOOLEAN` 선택

---

## 5. INNER JOIN vs LEFT JOIN

- **INNER JOIN**: 양쪽 테이블에 **둘 다 일치하는 행만** 반환. 한쪽에 없으면 그 행 자체가 결과에서 빠짐
- **LEFT JOIN**: 왼쪽 테이블 행은 **무조건 다 남기고**, 오른쪽에 일치하는 게 없으면 NULL로 채움
  - `Q8`이 LEFT JOIN인 이유: "대여 이력이 하나도 없는 회원"도 결과에 보여야 하니까 (INNER JOIN이었다면 그 회원은 아예 결과에서 사라짐)

---

## 6. 복잡 쿼리 단계별 분해 예시

```sql
SELECT title FROM book
WHERE book_id NOT IN (
    SELECT DISTINCT book_id FROM rental
);
```
1) 안쪽부터 실행: SELECT DISTINCT book_id FROM rental → 대여된 적 있는 book_id 목록을 먼저 뽑음
2) 바깥쪽 실행: book 테이블에서, 1번 목록에 없는 book_id만 골라냄
3) 즉 "대여 기록에 한 번도 등장하지 않은 책"을 찾는 것
---

## 7. 인덱스 선정 근거

* rental.member_id에 인덱스를 건 이유:

    - 조회 빈도: Q5, Q9처럼 "특정 회원의 대여 내역"을 찾는 쿼리가 가장 자주 실행될 걸로 예상
    - 카디널리티: member_id는 값의 종류가 많아서(회원 수만큼) 인덱스 효율이 좋음. 반대로 status(RENTED/RETURNED 두세 개뿐)처럼 값 종류가 적은 컬럼은 인덱스 효과가 작음 