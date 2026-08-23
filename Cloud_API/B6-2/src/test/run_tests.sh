#!/bin/bash
set -e
cd "$(dirname "$0")"

LOG_DIR=../logs
mkdir -p "$LOG_DIR"
TS=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/test.log"

python3 run_tests.py 2>&1 | tee "$LOG_FILE"

echo ""
echo "로그 저장 완료: test/$LOG_FILE"