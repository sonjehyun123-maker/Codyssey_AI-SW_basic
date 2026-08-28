PYTHON := python3
SCENARIO_DIR := ./data-make-test
LOG_DIR := logs
LOG_FILE := $(LOG_DIR)/test.txt

.PHONY: help all clean

help:
	@echo "make all    - 전체 기능 시나리오 실행 ($(LOG_FILE) 에 로그 저장, 덮어쓰기)"
	@echo "make clean  - data/캐시/export.csv 삭제"

all:
	@mkdir -p $(LOG_DIR)
	@{ \
		rm -rf $(SCENARIO_DIR); \
		echo "category(카테고리 관리):"; \
		echo "$$ category add"; \
		printf "salary\n" | $(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) category add; \
		echo "$$ category list"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) category list; \
		echo; \
		echo "add(거래추가):"; \
		echo "$$ add (1/3)"; \
		printf "2024-01-15\nexpense\nfood\n15000\n점심\nmeal\n" | $(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) add; \
		echo "$$ add (2/3)"; \
		printf "2024-01-14\nincome\nsalary\n3000000\n\n\n" | $(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) add; \
		echo "$$ add (3/3)"; \
		printf "2024-01-12\nexpense\ntransport\n20000\n\n\n" | $(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) add; \
		echo; \
		echo "list(거래 목록):"; \
		echo "$$ list --limit 5"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) list --limit 5; \
		echo; \
		echo "search(거래 검색):"; \
		echo "$$ search --type expense --from 2024-01-01 --to 2024-01-31"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) search --type expense --from 2024-01-01 --to 2024-01-31; \
		echo; \
		echo "budget + summary(예산/월별 요약):"; \
		echo "$$ budget set --month 2024-01 --amount 500000"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) budget set --month 2024-01 --amount 500000; \
		echo "$$ summary --month 2024-01 --top 3"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) summary --month 2024-01 --top 3; \
		echo; \
		echo "update(거래 수정):"; \
		echo "$$ update --id TX-000001 --amount 18000 --memo 점심(수정)"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) update --id TX-000001 --amount 18000 --memo "점심(수정)"; \
		echo; \
		echo "delete(거래 삭제):"; \
		echo "$$ delete --id TX-000003"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) delete --id TX-000003; \
		echo; \
		echo "export/import(내보내기/가져오기):"; \
		echo "$$ export --out export.csv --month 2024-01"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) export --out export.csv --month 2024-01; \
		echo "$$ import --from export.csv"; \
		$(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) import --from export.csv; \
		echo; \
		echo "오류 출력 예시:"; \
		echo "$$ add (잘못된 날짜)"; \
		printf "2024-13-40\nexpense\nfood\n15000\n\n\n" | $(PYTHON) -m budget_app --data-dir $(SCENARIO_DIR) add; \
		echo; \
		rm -rf $(SCENARIO_DIR) export.csv; \
		echo "[전체 시나리오 완료]"; \
	} 2>&1 | tee $(LOG_FILE)

clean:
	rm -rf ./data $(SCENARIO_DIR) export.csv budget_app/__pycache__ __pycache__