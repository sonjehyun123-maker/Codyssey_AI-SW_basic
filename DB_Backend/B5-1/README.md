# B5-1 SQL Database (PostgreSQL)

도서 대여 관리 시스템을 주제로 PostgreSQL의 기본 SQL 문법과 JOIN, GROUP BY, 서브쿼리, 인덱스를 학습하는 코디세이 미션입니다.

## 프로젝트 구조

<escape>B5-1/
├── 01_schema.sql
├── 02_sample_data.sql
├── 03_queries.sql
├── 04_query_results.txt
├── Makefile
└── README.md</escape>

## 기술 스택

* PostgreSQL 16
* Docker
* psql CLI

## 실행 환경

### PostgreSQL 컨테이너 생성

```bash
docker run --name codyssey-postgres \
  -e POSTGRES_USER=codyssey \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=library_db \
  -p 5432:5432 \
  -d postgres:16
```

### SQL 실행

```bash
docker exec -i codyssey-postgres psql -U codyssey -d library_db < 01_schema.sql
docker exec -i codyssey-postgres psql -U codyssey -d library_db < 02_sample_data.sql
docker exec -i codyssey-postgres psql -U codyssey -d library_db < 03_queries.sql
```

## 실행 검증 로그

### Docker 컨테이너 확인

```bash
docker ps
```

출력

```text
CONTAINER ID   IMAGE         STATUS   PORTS
6245e02e1180   postgres:16   Up       5432->5432
```

### 테이블 생성 확인

```sql
\dt
```

출력

```text
author
book
category
member
rental
```

총 5개의 테이블이 정상 생성되었습니다.

### rental 테이블 구조 확인

```sql
\d rental
```

확인 내용

* Primary Key: `rental_id`
* Foreign Key

  * `member_id`
  * `book_id`
* Index

  * `idx_rental_member_id`

### 데이터 확인

```sql
SELECT * FROM member;
```

결과

* 회원 데이터 12건 정상 조회

### 인덱스 확인

```sql
\di
```

생성된 인덱스

```text
idx_rental_member_id
```

## 성능 분석

### EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT *
FROM rental
WHERE member_id = 1;
```

결과

```text
Seq Scan on rental
Execution Time: 0.017 ms
```

### 왜 Index Scan이 아닌 Seq Scan인가?

`idx_rental_member_id` 인덱스를 생성했지만 PostgreSQL은 `Seq Scan`을 선택했습니다.

이유는 `rental` 테이블의 데이터가 약 13건으로 매우 적기 때문입니다.

PostgreSQL Query Planner는 작은 테이블에서는 인덱스를 사용하는 것보다 전체 테이블을 한 번 읽는 것이 더 빠르다고 판단합니다.

데이터가 많아질수록 `Index Scan`이 선택될 가능성이 높아집니다.

## 학습한 SQL 기능

* CREATE TABLE
* INSERT
* SELECT
* WHERE
* ORDER BY
* INNER JOIN
* LEFT JOIN
* GROUP BY
* COUNT
* NOT EXISTS
* UPDATE
* DELETE
* CREATE INDEX
* EXPLAIN ANALYZE

## 리팩토링 적용 사항

* `LEFT JOIN` 결과를 집계 형태로 개선
* `GROUP BY`를 기본키 기준으로 수정
* `NOT IN` → `NOT EXISTS`
* `UPDATE`, `DELETE` 안전 조건 추가
* `SELECT *` 최소화
* SQL 별칭(`AS`) 사용으로 가독성 향상

# 개념 보완 문서

## 1. DB와 엑셀의 차이

| | 엑셀 | 관계형 DB |
|---|---|---|
| 관계 표현 | 시트 간 연결 없음, 수동 VLOOKUP | FK로 테이블 간 관계를 강제 |
| 무결성 | 아무 값이나 입력 가능 | PK/FK/CHECK로 잘못된 값 자체를 차단 |
| 동시성 | 동시 편집 시 충돌/덮어쓰기 위험 | 트랜잭션으로 동시 접근을 안전하게 관리 |
| 검색/집계 | 수식으로 직접 계산 | SQL로 대량 데이터도 빠르게 질의 |

핵심: 엑셀은 "데이터를 보여주는 표"고, DB는 "데이터 간 관계와 규칙을 강제하는 시스템"이다.

## 2. PK와 FK의 역할

- **PK (Primary Key)** — 그 행의 "신원증명". 테이블 안에서 유일해야 하고 절대 중복/NULL 불가.
  - 예: `book.book_id` — 세상에 같은 제목의 책이 여러 권 있어도, `book_id`는 무조건 하나만 존재
- **FK (Foreign Key)** — 다른 테이블의 PK를 "참조"하는 값. 그 값이 실제로 존재하는지 DB가 검증해줌.
  - 예: `rental.book_id`는 `book.book_id`를 참조 → 존재하지 않는 `book_id`로 대여 기록을 넣으려 하면 DB가 거부함

즉 **PK = "나는 누구다"**, **FK = "나는 저것과 연결되어 있다"**.

## 3. 테이블을 왜 나눴는가

만약 `rental` 테이블 하나에 회원명, 책 제목, 카테고리명, 저자명을 다 때려박았다면:
- 같은 책이 100번 대여되면 책 제목·카테고리·저자 정보가 100번 중복 저장됨
- 책 제목에 오타가 있어서 고치려면 100개 행을 다 고쳐야 함 (수정 이상)
- 이래서 "책 정보는 `book`에 한 번만, `rental`은 `book_id`만 참조"하도록 분리함

**분리 기준**: "이 정보가 독립적으로 존재할 수 있는가?" → 책은 대여 기록이 없어도 존재할 수 있으니 별도 테이블.

## 4. 컬럼 타입 선정 이유

- `TEXT` vs `VARCHAR(n)` — PostgreSQL에서는 둘의 성능 차이가 없어서 길이 제한이 꼭 필요한 게 아니면 `TEXT`를 씀 (다른 DB, 예: MySQL은 다를 수 있음)
- `DATE` vs `TIMESTAMP` — 대여일/반납일은 "몇 시 몇 분"까지 필요 없고 "그 날짜"만 중요해서 `DATE`로 충분
- `BOOLEAN` (`is_available`) — 상태값이 참/거짓 두 가지뿐이라 `INTEGER`(1/0)보다 의미가 명확한 `BOOLEAN` 선택

## 5. INNER JOIN vs LEFT JOIN

- **INNER JOIN**: 양쪽 테이블에 **둘 다 일치하는 행만** 반환. 한쪽에 없으면 그 행 자체가 결과에서 빠짐
- **LEFT JOIN**: 왼쪽 테이블 행은 **무조건 다 남기고**, 오른쪽에 일치하는 게 없으면 NULL로 채움
  - `Q8`이 LEFT JOIN인 이유: "대여 이력이 하나도 없는 회원"도 결과에 보여야 하니까 (INNER JOIN이었다면 그 회원은 아예 결과에서 사라짐)

## 6. 복잡 쿼리 단계별 분해 예시

```sql
SELECT title FROM book
WHERE book_id NOT IN (
    SELECT DISTINCT book_id FROM rental
);
```
1. **안쪽부터 실행**: `SELECT DISTINCT book_id FROM rental` → 대여된 적 있는 book_id 목록을 먼저 뽑음
2. **바깥쪽 실행**: `book` 테이블에서, 1번 목록에 **없는** book_id만 골라냄
3. 즉 "대여 기록에 한 번도 등장하지 않은 책"을 찾는 것

## 7. 인덱스 선정 근거

`rental.member_id`에 인덱스를 건 이유:
- **조회 빈도**: `Q5`, `Q9`처럼 "특정 회원의 대여 내역"을 찾는 쿼리가 가장 자주 실행될 걸로 예상
- **카디널리티**: `member_id`는 값의 종류가 많아서(회원 수만큼) 인덱스 효율이 좋음. 반대로 `status`(RENTED/RETURNED 두세 개뿐)처럼 값 종류가 적은 컬럼은 인덱스 효과가 작음