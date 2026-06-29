#!/bin/bash
# system_monitor.sh - 시스템 관제 자동화 스크립트

PROCESS_NAME="agent-leak-app"
LOG_FILE="$HOME/agent_home/logs/agent.log"

# 환경변수 로드 및 초기화 확인
export MEMORY_LIMIT=512
export CPU_MAX_OCCUPY=20
export MULTI_THREAD_ENABLE=false

echo "[$(date)] 🔍 시스템 관제 자동화 스크립트 가동 시작..."

while true; do
    # 1. 프로세스 존재 여부 확인
    PID=$(pgrep -f "$PROCESS_NAME")
    
    if [ -z "$PID" ]; then
        echo "[ALERT] ⚠️ $PROCESS_NAME 프로세스가 다운되었습니다! 재시작을 시도합니다."
        ~/agent_home/$PROCESS_NAME &
        sleep 2; continue
    fi

    # 2. Case 1: OOM (메모리 누수) 관제
    # RSS 사용량을 MB 단위로 환산
    MEM_USAGE=$(ps -o rss= -p $PID | awk '{print int($1/1024)}')
    if [ "$MEM_USAGE" -ge "$MEMORY_LIMIT" ]; then
        echo "[CRITICAL] 🔥 메모리 임계치 초과 ($MEM_USAGE MB / $MEMORY_LIMIT MB). 서비스 재부팅으로 메모리를 확보합니다."
        kill -9 $PID
        sleep 1
        ~/agent_home/$PROCESS_NAME &
    fi

    # 3. Case 2: CPU 과점유 관제
    CPU_USAGE=$(ps -p $PID -o %cpu= | awk '{print int($1)}')
    if [ "$CPU_USAGE" -ge "$CPU_MAX_OCCUPY" ]; then
        echo "[WARNING] ⚡ CPU 점유율 임계치 경고! 현재 사용량: $CPU_USAGE%"
        # 실습 결과에 따라 내부 쿨링 메커니즘이 있으므로 모니터링 로그만 기록하거나 경고 알림 생성
    fi

    # 4. Case 3: 데드락 (Hang) 관제
    # WCHAN 상태가 do_wait 상태이거나 BLOCKED 로그가 단시간에 급증하는지 체크
    WCHAN_STATUS=$(ps -q $PID -o wchan=)
    DEADLOCK_LOG_COUNT=$(tail -n 10 $LOG_FILE 2>/dev/null | grep -c "Status: BLOCKED")
    
    if [ "$WCHAN_STATUS" == "do_wait" ] && [ "$DEADLOCK_LOG_COUNT" -gt 0 ]; then
        echo "[EMERGENCY] 🛑 데드락(교착 상태) 감지! 스레드가 멈췄습니다. 강제 덤프 후 정상 모드로 복구합니다."
        # 환경변수 조치 후 재시작
        kill -9 $PID
        export MULTI_THREAD_ENABLE=false
        ~/agent_home/$PROCESS_NAME &
    fi

    sleep 3
done