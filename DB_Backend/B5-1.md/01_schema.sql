-- ============================================
-- 도서 대여 관리 데이터베이스 - 스키마 생성 스크립트
-- 대상 DB: PostgreSQL
-- 실행: psql -U postgres -d book_rental_db -f 01_schema.sql
-- 실행 순서: 이 파일 -> 02_sample_data.sql -> 03_queries.sql
-- ============================================

DROP TABLE IF EXISTS rental;
DROP TABLE IF EXISTS book;
DROP TABLE IF EXISTS author;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS member;

-- --------------------------------------------
-- 1. category : 도서 카테고리
-- --------------------------------------------
CREATE TABLE category (
    category_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name   TEXT NOT NULL UNIQUE
);

-- --------------------------------------------
-- 2. author : 저자
-- --------------------------------------------
CREATE TABLE author (
    author_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_name     TEXT NOT NULL
);

-- --------------------------------------------
-- 3. member : 회원
-- --------------------------------------------
CREATE TABLE member (
    member_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_name     TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    phone           TEXT,
    joined_at       DATE NOT NULL
);

-- --------------------------------------------
-- 4. book : 도서 (category : book = 1:N, author : book = 1:N)
-- --------------------------------------------
CREATE TABLE book (
    book_id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title           TEXT NOT NULL,
    isbn            TEXT NOT NULL UNIQUE,
    published_year  INTEGER,
    category_id     INTEGER NOT NULL,
    author_id       INTEGER NOT NULL,
    is_available    BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES category(category_id),
    FOREIGN KEY (author_id) REFERENCES author(author_id)
);

-- --------------------------------------------
-- 5. rental : 대여 기록 (member : rental = 1:N, book : rental = 1:N)
-- --------------------------------------------
CREATE TABLE rental (
    rental_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id       INTEGER NOT NULL,
    book_id         INTEGER NOT NULL,
    rental_date     DATE NOT NULL,
    due_date        DATE NOT NULL,
    return_date     DATE,
    status          TEXT NOT NULL DEFAULT 'RENTED',  -- RENTED / RETURNED / OVERDUE
    FOREIGN KEY (member_id) REFERENCES member(member_id),
    FOREIGN KEY (book_id) REFERENCES book(book_id)
);
