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
