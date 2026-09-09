-- ============================================
-- 도서 대여 관리 데이터베이스 - 핵심 쿼리 15개
-- 실행 순서: 01_schema.sql -> 02_sample_data.sql -> 이 파일
-- ============================================

-- ============ [기본 조회 4개] ============

-- Q1. 대여 가능한(is_available=TRUE) 책을 출간연도 최신순으로 5권 조회
SELECT title, published_year
FROM book
WHERE is_available = TRUE
ORDER BY published_year DESC
LIMIT 5;

-- Q2. 이메일이 example.com 도메인인 회원 조회
SELECT member_name, email
FROM member
WHERE email LIKE '%@example.com';

-- Q3. 2026년 7월에 발생한 대여 기록만 조회
SELECT rental_id, member_id, book_id, rental_date, status
FROM rental
WHERE rental_date BETWEEN '2026-07-01' AND '2026-07-31'
ORDER BY rental_date;

-- Q4. 아직 반납되지 않은(RENTED) 대여 목록을 반납예정일 순으로 조회
SELECT rental_id, member_id, book_id, due_date, status
FROM rental
WHERE status = 'RENTED'
ORDER BY due_date;


-- ============ [조인 4개] ============

-- Q5. (INNER JOIN) 회원명과 함께 대여 내역 조회
SELECT r.rental_id, m.member_name, r.rental_date, r.status
FROM rental r
INNER JOIN member m ON r.member_id = m.member_id
ORDER BY r.rental_date;

-- Q6. (INNER JOIN, 3-way) 대여별 회원명 + 책 제목 상세 조회
SELECT r.rental_id, m.member_name, b.title, r.rental_date, r.due_date
FROM rental r
INNER JOIN member m ON r.member_id = m.member_id
INNER JOIN book b ON r.book_id = b.book_id
ORDER BY r.rental_id;

-- Q7. (INNER JOIN) 책 목록에 카테고리명 + 저자명 함께 조회
SELECT b.title, cat.category_name, a.author_name
FROM book b
INNER JOIN category cat ON b.category_id = cat.category_id
INNER JOIN author a ON b.author_id = a.author_id
ORDER BY cat.category_name, b.title;

-- Q8. (LEFT JOIN) 전체 회원과 대여 건수 조회 (대여 없는 회원 포함)
SELECT
    m.member_name,
    COUNT(r.rental_id) AS rental_count
FROM member AS m
LEFT JOIN rental AS r
    ON m.member_id = r.member_id
GROUP BY m.member_id, m.member_name
ORDER BY m.member_name;


-- ============ [집계 3개] ============

-- Q9. (COUNT + GROUP BY) 회원별 대여 횟수 집계
SELECT
    m.member_name,
    COUNT(r.rental_id) AS rental_count
FROM member AS m
INNER JOIN rental AS r
    ON m.member_id = r.member_id
GROUP BY m.member_id, m.member_name
ORDER BY rental_count DESC, m.member_name;

-- Q10. (COUNT + GROUP BY) 카테고리별 보유 도서 수 집계
SELECT
    cat.category_name,
    COUNT(b.book_id) AS book_count
FROM category AS cat
LEFT JOIN book AS b
    ON cat.category_id = b.category_id
GROUP BY cat.category_id, cat.category_name
ORDER BY book_count DESC, cat.category_name;

-- Q11. (COUNT + GROUP BY) 카테고리별 대여 횟수 집계 (인기 카테고리 파악)
SELECT
    cat.category_name,
    COUNT(r.rental_id) AS rental_count
FROM category AS cat
LEFT JOIN book AS b
    ON cat.category_id = b.category_id
LEFT JOIN rental AS r
    ON b.book_id = r.book_id
GROUP BY cat.category_id, cat.category_name
ORDER BY rental_count DESC, cat.category_name;


-- ============ [서브쿼리 1개] ============

-- Q12. 한 번도 대여되지 않은 책 찾기 (NOT IN 서브쿼리)
SELECT b.title
FROM book AS b
WHERE NOT EXISTS (
    SELECT 1
    FROM rental AS r
    WHERE r.book_id = b.book_id
);

-- ============ [데이터 수정/삭제 2개] ============

-- Q13. (UPDATE) 3번 대여 기록을 반납 완료 처리
UPDATE rental
SET
    status = 'RETURNED',
    return_date = '2026-07-10'
WHERE rental_id = 4
  AND status = 'RENTED';

-- Q14. (DELETE) 반납 완료된 대여 기록 중 2026년 6월 이전에 반납된 오래된 기록 삭제
DELETE FROM rental
WHERE status = 'RETURNED'
  AND return_date IS NOT NULL
  AND return_date < '2026-06-15';

-- ============ [인덱스 1개] ============

-- Q15. rental.member_id 인덱스 생성
-- 이유: "회원별 대여 조회(Q5, Q9)"처럼 member_id로 rental을 찾는 조회가
--       매우 빈번한 FK 컬럼이므로, 인덱스를 걸어 조회 성능을 개선한다.
CREATE INDEX idx_rental_member_id ON rental(member_id);