# B5-1 PostgreSQL 재현 가이드

이 문서는 macOS + Docker 환경에서 B5-1 도서 대여 관리 데이터베이스를 처음부터 다시 실행하는 방법을 기록한다.

## 환경

* macOS
* Docker 28.x
* PostgreSQL 16

---

## 1. Docker 확인

버전 확인

```bash
docker -v
```

예상 출력

```text
Docker version 28.x
```

Docker 실행 여부 확인

```bash
docker ps
```

---

## 2. PostgreSQL 컨테이너 생성

```bash
docker run --name codyssey-postgres \
  -e POSTGRES_USER=codyssey \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=library_db \
  -p 5432:5432 \
  -d postgres:16
```

확인

```bash
docker ps
```

예상 출력

```text
codyssey-postgres   postgres:16   Up
```

---

## 3. 프로젝트 폴더 이동

```bash
cd ~/Codyssey_AI-SW_basic/DB_Backend/B5-1
```

파일 확인

```bash
ls
```

예상 출력

```text
01_schema.sql
02_sample_data.sql
03_queries.sql
04_query_results.txt
README.md
```

---

## 4. 데이터베이스 생성

스키마 생성

```bash
docker exec -i codyssey-postgres \
psql -U codyssey -d library_db < 01_schema.sql
```

예상 출력

```text
CREATE TABLE
```

---

## 5. 샘플 데이터 삽입

```bash
docker exec -i codyssey-postgres \
psql -U codyssey -d library_db < 02_sample_data.sql
```

예상 출력

```text
INSERT 0 10
INSERT 0 12
...
```

---

## 6. 쿼리 실행

```bash
docker exec -i codyssey-postgres \
psql -U codyssey -d library_db < 03_queries.sql
```

예상 결과

* SELECT 결과 출력
* UPDATE 1
* DELETE 2
* CREATE INDEX

---

## 7. PostgreSQL 접속

```bash
docker exec -it codyssey-postgres \
psql -U codyssey -d library_db
```

프롬프트

```text
library_db=#
```

---

## 8. 검증

### 테이블 목록

```sql
\dt
```

예상 결과

```text
author
book
category
member
rental
```

### rental 구조

```sql
\d rental
```

확인 항목

* Primary Key
* Foreign Key
* Index

### 인덱스 확인

```sql
\di
```

확인

```text
idx_rental_member_id
```

### 회원 데이터 확인

```sql
SELECT * FROM member;
```

예상 결과

* 12명의 회원 조회

---

## 9. 실행 계획 확인

```sql
EXPLAIN ANALYZE
SELECT *
FROM rental
WHERE member_id = 1;
```

예상 결과

```text
Seq Scan on rental
```

### 이유

현재 데이터가 적기 때문에 PostgreSQL Query Planner가 전체 스캔이 더 빠르다고 판단한다.

학습용으로 Index Scan 확인

```sql
SET enable_seqscan = OFF;

EXPLAIN ANALYZE
SELECT *
FROM rental
WHERE member_id = 1;

SET enable_seqscan = ON;
```

---

## 10. 자주 사용하는 명령어

| 명령                      | 설명     |
| ----------------------- | ------ |
| `\dt`                   | 테이블 목록 |
| `\d table`              | 테이블 구조 |
| `\di`                   | 인덱스 목록 |
| `SELECT * FROM member;` | 데이터 확인 |
| `EXPLAIN ANALYZE`       | 실행 계획  |
| `\q`                    | 종료     |

---

## 11. 컨테이너 관리

중지

```bash
docker stop codyssey-postgres
```

시작

```bash
docker start codyssey-postgres
```

삭제

```bash
docker rm -f codyssey-postgres
```

다시 처음부터 실행하려면 삭제 후 2번부터 진행하면 된다.

---

## 재현 체크리스트

* [ ] Docker 설치 확인
* [ ] PostgreSQL 컨테이너 실행
* [ ] `01_schema.sql` 실행
* [ ] `02_sample_data.sql` 실행
* [ ] `03_queries.sql` 실행
* [ ] `\dt`로 테이블 확인
* [ ] `\di`로 인덱스 확인
* [ ] `EXPLAIN ANALYZE` 실행
* [ ] 컨테이너 재시작 확인
