# B5-1 SQL Database (PostgreSQL)

도서 대여 관리 시스템을 주제로 PostgreSQL의 기본 SQL 문법과 JOIN, GROUP BY, 서브쿼리, 인덱스를 학습하는 코디세이 미션입니다.

## 프로젝트 구조 및 스키마

### 프로젝트 구조

```
B5-1/
├── 01_schema.sql
├── 02_sample_data.sql
├── 03_queries.sql
├── 04_query_results.txt
├── Makefile
└── README.md
```

### 테이블 관계도

![관계도](/DB_Backend/B5-1/images/image.png)

### 테이블 구조

| 테이블 | 역할 | PK | FK |
|---|---|---|---|
| `category` | 도서 카테고리 | category_id | - |
| `author` | 저자 | author_id | - |
| `member` | 회원 | member_id | - |
| `book` | 도서 | book_id | category_id → category, author_id → author |
| `rental` | 대여 기록 | rental_id | member_id → member, book_id → book |

**1:N 관계 4개**: `category → book`, `author → book`, `member → rental`, `book → rental`

### 제약조건

- **NOT NULL**: 모든 필수 컬럼 (`title`, `member_name`, `rental_date` 등)
- **UNIQUE**: `category.category_name`, `member.email`, `book.isbn`
- **FK 무결성**: 존재하지 않는 참조값으로는 INSERT 불가 (실제로 psql에서 위반 INSERT 시도해 에러 확인함)
- **인덱스**: `rental.member_id`에 B-tree 인덱스 생성 — 회원별 대여 조회가 가장 빈번한 패턴이고, member_id는 카디널리티가 높아 인덱스 효율이 좋음

## 개발 환경

### 기술 스택

- PostgreSQL 16
- Docker
- psql CLI

### 실행 환경

- **DB**: PostgreSQL 18
- **개발 환경**: Docker
  - 로컬 OS(Windows/macOS)를 오가며 작업하기 때문에, OS마다 설치 방법이 갈리는 네이티브 설치 대신 **컨테이너 이미지 하나로 어느 환경에서든 동일하게 재현**하기 위해 Docker를 선택함
  - `docker run` 명령어 한 줄로 즉시 기동/삭제가 가능해, 실습 중 스키마를 여러 번 갈아엎는 과정에서도 환경을 깔끔하게 초기화하기 용이함

```bash
docker run --name book-rental-pg \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  -d postgres:18
```

## SQL 학습 내용

### 학습한 SQL 기능

- CREATE TABLE
- INSERT
- SELECT
- WHERE
- ORDER BY
- INNER JOIN
- LEFT JOIN
- GROUP BY
- COUNT
- NOT EXISTS
- UPDATE
- DELETE
- CREATE INDEX
- EXPLAIN ANALYZE

### 쿼리 15개 구성

- 기본 조회 4개 (WHERE, ORDER BY, LIMIT)
- 조인 4개 (INNER JOIN 3개, LEFT JOIN 1개)
- 집계 3개 (COUNT 2개, AVG 1개 + GROUP BY)
- 서브쿼리 1개 (대여된 적 없는 도서 조회)
- 데이터 수정/삭제 2개 (UPDATE, DELETE)
- 인덱스 1개

### 리팩토링 적용 사항

- `LEFT JOIN` 결과를 집계 형태로 개선
- `GROUP BY`를 기본키 기준으로 수정
- `NOT IN` → `NOT EXISTS`
- `UPDATE`, `DELETE` 안전 조건 추가
- `SELECT *` 최소화
- SQL 별칭(`AS`) 사용으로 가독성 향상

### 개념 정리

정규화, PK/FK 역할, 인덱스(B+tree) 내부 구조, 트랜잭션 원자성, CHECK 제약조건 동작, DB 선택 기준 등은 `CONCEPTS_NOTES.md`에 정리함.

## 성능 분석

### EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT *
FROM rental
WHERE member_id = 1;
```

결과:

```text
Seq Scan on rental
Execution Time: 0.017 ms
```

### 왜 Index Scan이 아닌 Seq Scan인가?

`idx_rental_member_id` 인덱스를 생성했지만 PostgreSQL은 `Seq Scan`을 선택했습니다. 이유는 `rental` 테이블의 데이터가 약 13건으로 매우 적기 때문입니다. PostgreSQL Query Planner는 작은 테이블에서는 인덱스를 사용하는 것보다 전체 테이블을 한 번 읽는 것이 더 빠르다고 판단합니다. 데이터가 많아질수록 `Index Scan`이 선택될 가능성이 높아집니다.

## 제출 및 실행

### 제출 파일 구성

| 파일 | 내용 |
|---|---|
| `01_schema.sql` | CREATE TABLE, PK/FK/제약조건 |
| `02_sample_data.sql` | 테이블당 10행 이상 샘플 데이터 |
| `03_queries.sql` | 핵심 쿼리 15개 |
| `04_query_results.txt` | 쿼리별 실행 결과 |
| `CONCEPTS_NOTES.md` | 개념 학습 정리 (정규화/인덱스/트랜잭션 등) |
| `Makefile` | `make all`로 DB 생성 → 스키마 → 데이터 → 쿼리 한번에 실행 |

### 실행 방법

```bash
make all
```