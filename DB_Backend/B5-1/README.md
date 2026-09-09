# B5-1 SQL Database

도서 대여 관리 시스템을 주제로 SQL 기본 문법과 JOIN, GROUP BY, 서브쿼리, 데이터 수정 및 인덱스를 학습하는 코디세이 미션입니다.

## 프로젝트 구조

<escape>B5-1.md/
├── 01_schema.sql
├── 02_sample_data.sql
├── 03_queries.sql
├── 04_query_results.txt
├── Makeflie
└── README.md</escape>

## 실행 순서

1. `01_schema.sql`
2. `02_sample_data.sql`
3. `03_queries.sql`

## 포함된 SQL 기능

| 기능   | 내용                     |
| ---- | ---------------------- |
| DDL  | CREATE TABLE           |
| DML  | INSERT, UPDATE, DELETE |
| 조회   | SELECT, WHERE          |
| 정렬   | ORDER BY               |
| 조인   | INNER JOIN, LEFT JOIN  |
| 집계   | COUNT, GROUP BY        |
| 서브쿼리 | NOT EXISTS             |
| 성능   | INDEX                  |

## 리팩토링 적용 사항

* `LEFT JOIN` 결과를 집계 형태로 개선
* `GROUP BY`를 기본키 기준으로 수정
* `NOT IN` → `NOT EXISTS`
* `UPDATE`, `DELETE` 안전 조건 추가
* 정렬 기준을 명확하게 지정
* SQL 별칭(`AS`) 사용으로 가독성 향상

## 학습 포인트

* JOIN으로 여러 테이블 연결하기
* GROUP BY와 COUNT로 통계 만들기
* 서브쿼리 활용하기
* 인덱스로 조회 성능 개선하기
