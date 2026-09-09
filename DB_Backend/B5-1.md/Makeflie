DB_NAME := book_rental_db
DB_USER := postgres
DB_HOST := localhost
PSQL := PGPASSWORD=postgres psql -U $(DB_USER) -h $(DB_HOST) -d $(DB_NAME)

.PHONY: all createdb schema data queries reset dropdb psql

all: createdb schema data queries

createdb:
	PGPASSWORD=postgres createdb -U $(DB_USER) -h $(DB_HOST) $(DB_NAME) 2>/dev/null || true

schema:
	$(PSQL) -f 01_schema.sql

data:
	$(PSQL) -f 02_sample_data.sql

queries:
	$(PSQL) -f 03_queries.sql

reset: schema data

dropdb:
	PGPASSWORD=postgres dropdb -U $(DB_USER) -h $(DB_HOST) $(DB_NAME) 2>/dev/null || true

psql:
	$(PSQL)