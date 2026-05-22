# 시스템 관제 자동화 스크립트 개발
## 미션 소개
> **"로그가 없는 서버 장애 복구는 '감'에 의존하게 되며, 이는 장애 반복의 원인이 됩니다."**
> 리눅스는 현대 서버 환경의 표준입니다. 
* 다중 사용자 권한 관리
* 네트워크 보안
* 시스템 리소스 관제 및 로그 자동화
* 쉘 스크립트를 설계 및 구축
> 최종적으로 애플리케이션 배포 환경 안정화 및 시스템 상태를 데이터로 기록·관제할 수 있는 백엔드 엔지니어링 역량을 확보
### 미션 목적
 * "지속적으로 살아 움직이는 Runtime System" 구현

### 디렉토리 형태
```bash
/home/agent-admin/agent-app/                # AGENT_HOME (애플리케이션 루트)
├── bin/                                    # 실행 및 운영 스크립트 디렉토리
│   ├── monitor.sh                          # 시스템 관제 자동화 스크립트
│   └── stats.dat                           # CPU/MEM 통계 누적 데이터
│
├── api_keys/                               # 민감 정보 저장 디렉토리
│   └── t_secret.key                        # 애플리케이션 인증용 API Key
│
├── upload_files/                           # 사용자 업로드 및 협업 공유 디렉토리
│   └── (uploaded files...)                 # 업로드 파일 저장 위치
│
├── agent_app.py                            # 메인 애플리케이션 프로세스
│
├── .env                                    # 환경 변수 설정 파일 (선택 사용)
│
└── logs/                                   # 애플리케이션 내부 로그 디렉토리 (선택)
    └── app.log                             # 앱 실행 로그

/var/log/agent-app/                         # 시스템 운영 로그 디렉토리
├── monitor.log                             # 현재 활성 모니터링 로그
├── monitor.log.1                           # Rotation된 이전 로그
├── monitor.log.2                           # 이전 세대 로그
├── ...
└── monitor.log.10                          # 가장 오래된 보관 로그
```
---

# 1. 기본 보안 및 네트워크 설정

## SSH 포트 변경(20022) 및 Root 원격 접속 차단 설정 확인 내역

* SSH(Secure Shell) : 원격 시스템 접속 및 명령 실행을 위한 보안 네트워크 프로토콜

```bash
# 1. SSH 설정 파일 수정
sudo nano /etc/ssh/sshd_config

# 수정 내용
Port 20022
PermitRootLogin no

# 2. SSH 서비스 재시작
sudo systemctl restart ssh

# 3. SSH 서비스 상태 확인
sudo systemctl status ssh

# 4. 설정값 확인
grep -E 'Port|PermitRootLogin' /etc/ssh/sshd_config

# 결과
# Port 20022
# PermitRootLogin no

# 5. 포트 리슨 상태 확인
ss -tulnp | grep ssh

# 결과
# tcp   LISTEN 0      4096         0.0.0.0:20022      0.0.0.0:*    users:(("sshd",pid=xxx))
# tcp   LISTEN 0      4096            [::]:20022         [::]:*    users:(("sshd",pid=xxx))
```

### 보안 적용 이유

```text
기본 SSH 포트(22)는 인터넷 스캐닝 및 brute-force 공격의 주요 대상이다.

SSH 포트를 20022로 변경함으로써 자동화된 스캔 노출을 일부 감소시킬 수 있다.

또한 Root 원격 로그인을 차단하여,
공격자가 root 계정을 직접 대상으로 credential attack을 수행하는 위험을 줄였다.

이는 공격 표면 감소(reduce attack surface) 전략에 해당한다.
```

---

## 방화벽(UFW) 활성화 및 허용 포트 설정

* 허용 포트

  * TCP 20022 (SSH)
  * TCP 15034 (APP)

```bash
# 1. UFW 설치
sudo apt install ufw -y

# 2. 기본 정책 설정
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 3. SSH 포트 허용
sudo ufw allow 20022/tcp

# 4. APP 포트 허용
sudo ufw allow 15034/tcp

# 5. 방화벽 활성화
sudo ufw enable

# 결과
# Firewall is active and enabled on system startup

# 6. 방화벽 상태 확인
sudo ufw status verbose

# 결과
# Status: active
#
# To                         Action      From
# --                         ------      ----
# 20022/tcp                  ALLOW IN    Anywhere
# 15034/tcp                  ALLOW IN    Anywhere
# 20022/tcp (v6)             ALLOW IN    Anywhere (v6)
# 15034/tcp (v6)             ALLOW IN    Anywhere (v6)
```

---

# 2. 계정/그룹/권한 체계(협업 + 최소 권한)

## 계정 및 그룹 생성 

| 그룹명 | 포함 사용자 | 역할 | 접근 가능 영역 | 주요 권한 |
|---|---|---|---|---|
| agent-common | agent-admin<br>agent-dev<br>agent-test | 협업 및 공용 작업 그룹 | upload_files | 파일 업로드, 조회, 수정 가능 |
| agent-core | agent-admin<br>agent-dev | 핵심 운영/보안 그룹 | api_keys<br>/var/log/agent-app<br>monitor.sh | API Key 관리, 로그 관리, monitor.sh 실행 및 수정 |
```bash
# 1. 그룹 생성
sudo groupadd agent-common
sudo groupadd agent-core

# 2. 사용자 생성
sudo useradd -m -g agent-common -G agent-core agent-admin
sudo useradd -m -g agent-common -G agent-core agent-dev
sudo useradd -m -g agent-common agent-test

# 3. 사용자 정보 확인
id agent-admin
id agent-dev
id agent-test

# 결과
# agent-admin : uid=1001(agent-admin) gid=1001(agent-common) groups=1001(agent-common),1002(agent-core)
# agent-dev   : uid=1002(agent-dev) gid=1001(agent-common) groups=1001(agent-common),1002(agent-core)
# agent-test  : uid=1003(agent-test) gid=1001(agent-common) groups=1001(agent-common)

# 4. 그룹 확인
grep -E 'agent-common|agent-core' /etc/group
```

---

## 디렉토리 구조 및 권한(ACL 포함) 확인 내역

* ACL(Access Control List) : 추가 접근 권한 제어 기능

```bash
# 1. AGENT_HOME 생성
sudo mkdir -p /home/agent-admin/agent-app

# 2. 디렉토리 생성
sudo mkdir -p /home/agent-admin/agent-app/upload_files
sudo mkdir -p /home/agent-admin/agent-app/api_keys
sudo mkdir -p /home/agent-admin/agent-app/bin
sudo mkdir -p /var/log/agent-app

# 3. 그룹 설정
sudo chown -R agent-admin:agent-common /home/agent-admin/agent-app/upload_files
sudo chown -R agent-admin:agent-core /home/agent-admin/agent-app/api_keys
sudo chown -R agent-admin:agent-core /var/log/agent-app

# 4. 권한 설정 (setgid 적용)
sudo chmod 2770 /home/agent-admin/agent-app/upload_files
sudo chmod 2770 /home/agent-admin/agent-app/api_keys
sudo chmod 2770 /var/log/agent-app

# AGENT_HOME 권한 제한
sudo chmod 750 /home/agent-admin/agent-app

# 5. ACL 설정
sudo setfacl -m u:agent-test:rwx /home/agent-admin/agent-app/upload_files
sudo setfacl -m u:agent-test:--- /home/agent-admin/agent-app/api_keys

# 6. 권한 확인
ls -ld /home/agent-admin/agent-app/upload_files
ls -ld /home/agent-admin/agent-app/api_keys
ls -ld /var/log/agent-app

# 결과
# drwxrws---+ 2 agent-admin agent-common 4096 May 8 21:50 upload_files
# drwxrws---+ 2 agent-admin agent-core   4096 May 8 21:50 api_keys
# drwxrws---+ 2 agent-admin agent-core   4096 May 8 21:50 agent-app

# 7. ACL 확인
getfacl /home/agent-admin/agent-app/upload_files
getfacl /home/agent-admin/agent-app/api_keys
```

### 최소 권한 원칙 적용 이유

```text
api_keys와 로그 디렉토리는 운영 핵심 데이터 영역이다.

따라서 agent-core 그룹만 접근 가능하도록 제한하였다.

특히 agent-test 계정은 테스트 목적 계정이므로:
- API Key
- 운영 로그
- 민감 설정
등에 접근하지 못하도록 분리하였다.

이는 Least Privilege Principle(최소 권한 원칙)을 적용한 것이다.
```

### setgid(특수권한) 적용 이유

```text
setgid(2)를 적용하여 디렉토리 내부에서 새로 생성되는 파일과 디렉토리가
상위 디렉토리의 그룹(agent-common 또는 agent-core)을 자동 상속하도록 구성하였다.

이를 통해 협업 환경에서 그룹 권한 일관성을 유지할 수 있다.
```

---

# 3. 애플리케이션 실행 환경 구성

## 환경 변수 설정

```bash
sudo su - agent-admin

nano ~/.bashrc

# 추가
export AGENT_HOME="/home/agent-admin/agent-app"
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR="$AGENT_HOME/upload_files"
export AGENT_KEY_PATH="$AGENT_HOME/api_keys/t_secret.key"
export AGENT_LOG_DIR="/var/log/agent-app"

# 적용
source ~/.bashrc
```

---

## 키 파일 생성

```bash
mkdir -p $AGENT_HOME/api_keys

echo "agent_api_key_test" > $AGENT_KEY_PATH

cat $AGENT_KEY_PATH

# 결과
# agent_api_key_test

sudo mkdir -p $AGENT_LOG_DIR
sudo chown agent-admin:agent-core $AGENT_LOG_DIR
sudo chmod 2770 $AGENT_LOG_DIR
```

---

## 앱 실행 및 성공 기준

* 일반 계정으로 실행(루트 실행 금지)
* Boot Sequence 5단계가 모두 [OK] 출력
* 마지막에 “Agent READY” 출력
* 0.0.0.0:15034 LISTEN 상태 확인

```bash
cd $AGENT_HOME

# 제공된 Python 앱 실행
python3 provided_agent_app.py
```

### 실행 결과

```text
> Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]
[2/5] Verifying Environment Variables     [OK]
[3/5] Checking Required Files             [OK]
[4/5] Checking Port Availability          [OK]
[5/5] Verifying Log Permission            [OK]
------------------------------------------------------------
All Boot Checks Passed!
Agent READY
Listening on 0.0.0.0:15034
```

### LISTEN 상태 확인

```bash
ss -tulnp | grep 15034
```

---

# 4. 시스템 관제 자동화 스크립트(monitor.sh) 구현

## monitor.sh 파일 생성

```bash
cd $AGENT_HOME/bin
nano monitor.sh
```

### monitor.sh 코드

```bash
#!/bin/bash

export AGENT_HOME="/home/agent-admin/agent-app"
APP_NAME="agent_app.py"
PORT=15034
LOG_FILE="/var/log/agent-app/monitor.log"
STATS_FILE="$AGENT_HOME/bin/stats.dat"

# 통계 파일 생성
touch "$STATS_FILE"

echo "====== SYSTEM MONITOR RESULT ======"

echo -e "\n[HEALTH CHECK]"

PID=$(pgrep -fo "$APP_NAME")

if [ -z "$PID" ]; then
    echo "Checking process '$APP_NAME'... [FAIL]"
    exit 1
fi

echo "Checking process '$APP_NAME'... [OK] (PID: $PID)"

if ! ss -tuln | grep LISTEN | grep -q ":$PORT "; then
    echo "Checking port $PORT... [FAIL]"
    exit 1
fi

echo "Checking port $PORT... [OK]"

# 방화벽 상태 점검
UFW_CHECK=$(ufw status | grep "Status: active")

if [ -z "$UFW_CHECK" ]; then
    echo "[WARNING] Firewall is inactive."
fi

# 자원 수집
CPU=$(top -bn1 | awk '/Cpu/ {print 100 - $8}')          # 사용률 = 100 - idle
MEM=$(free | grep Mem | awk '{print $3/$2 * 100.0}')    # 사용 메모리 / 전체 메모리 * 100
DISK=$(df / | tail -1 | awk '{print $5}' | sed 's/%//') # df에서 디스크 사용량을 %빼고 추출

echo -e "\n[RESOURCE MONITORING]"
printf "CPU Usage : %.1f%%\n" "$CPU"
printf "MEM Usage : %.1f%%\n" "$MEM"
echo "DISK Used  : $DISK%"

# 임계값 경고
[[ $(echo "$CPU > 20" | bc -l) -eq 1 ]] && echo "[WARNING] CPU threshold exceeded ($CPU% > 20%)"
[[ $(echo "$MEM > 10" | bc -l) -eq 1 ]] && echo "[WARNING] MEM threshold exceeded ($MEM% > 10%)"
[ "$DISK" -gt 80 ] && echo "[WARNING] DISK_USED threshold exceeded ($DISK% > 80%)"

# 통계 기록
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "$TIMESTAMP $CPU $MEM" >> "$STATS_FILE"

# 로그 기록
LOG_LINE="[$TIMESTAMP] PID:$PID CPU:$(printf "%.1f" $CPU)% MEM:$(printf "%.1f" $MEM)% DISK_USED:$DISK%"

echo "$LOG_LINE" >> "$LOG_FILE"

# 로그 로테이션
MAX_SIZE=$((10 * 1024 * 1024))

if [ $(stat -c%s "$LOG_FILE") -gt $MAX_SIZE ]; then
    for i in {9..1}; do
        [ -f "$LOG_FILE.$i" ] && mv "$LOG_FILE.$i" "$LOG_FILE.$((i+1))"
    done

    mv "$LOG_FILE" "$LOG_FILE.1"

    touch "$LOG_FILE"
    chown agent-admin:agent-core "$LOG_FILE"
    chmod 660 "$LOG_FILE"
fi

echo -e "\n[INFO] Log appended: $LOG_FILE"
```

---

## monitor.sh 소유권 및 권한 설정

```bash
sudo chown agent-dev:agent-core $AGENT_HOME/bin/monitor.sh
sudo chmod 750 $AGENT_HOME/bin/monitor.sh
```

### 권한 확인

```bash
ls -l $AGENT_HOME/bin/monitor.sh
```

예시 결과:

```text
-rwxr-x--- 1 agent-dev agent-core 4096 May 11 15:00 monitor.sh
```

### 권한 정책 설명

```text
monitor.sh의 소유자는 agent-dev,
실행 그룹은 agent-core로 설정하였다.

cron 실행 계정(agent-admin)은 agent-core 그룹에 포함되어 있으므로 실행 가능하다.

권한 750을 적용하여:
- owner(agent-dev): 읽기/쓰기/실행
- group(agent-core): 읽기/실행
- others: 접근 불가
정책을 적용하였다.
```

---

## monitor.sh 실행 결과

```bash
/home/agent-admin/agent-app/bin/monitor.sh
```

### 결과

```text
====== SYSTEM MONITOR RESULT ======

[HEALTH CHECK]
Checking process 'agent_app.py'... [OK] (PID: 10119)
Checking port 15034... [OK]

[RESOURCE MONITORING]
CPU Usage : 3.0%
MEM Usage : 7.3%
DISK Used  : 1%

[INFO] Log appended: /var/log/agent-app/monitor.log
```

---

## 비정상 상태 Exit 1 확인

```bash
pkill -f agent_app.py

/home/agent-admin/agent-app/bin/monitor.sh

echo $?
```

### 결과

```text
Checking process 'agent_app.py'... [FAIL]
1
```

### 설계 이유

```text
프로세스 비정상 종료 및 포트 미오픈 상태는 서비스 장애로 판단하여 즉시 exit 1 처리하였다.

반면 방화벽 비활성 상태나 CPU/MEM 임계치 초과는 즉시 서비스 불능 상태는 아닐 수 있으므로,
운영자가 추후 확인할 수 있도록 WARNING만 출력하도록 설계하였다.

즉:
- Hard Failure → exit
- Soft Warning → logging
으로 구분하였다.
```

---

# 5. 로그 기록 및 자동 실행(cron)

## monitor.log 확인

```bash
tail -n 5 /var/log/agent-app/monitor.log
```

### 결과

```text
[2026-05-13 19:29:55] PID:10119 CPU:1.2% MEM:7.3% DISK_USED:1%
[2026-05-13 19:30:01] PID:10119 CPU:1.2% MEM:7.3% DISK_USED:1%
[2026-05-13 19:31:02] PID:10119 CPU:1.2% MEM:7.3% DISK_USED:1%
```

---

## cron 자동 실행 등록

```bash
sudo su - agent-admin

crontab -e
```

### 등록 내용

```cron
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/cron.log 2>&1
```

### 등록 확인

```bash
crontab -l
```

### 결과

```text
* * * * * /home/agent-admin/agent-app/bin/monitor.sh >> /var/log/agent-app/cron.log 2>&1
```

* crontab 주기 실행과 로그 보존 정책이 왜 필요한가
모니터링은 사람이 수동으로 실행하면 의미가 없음. 자동으로 주기 실행해야 문제를 놓치지 않기 때문. 또한 로그를 무한개로 쌓으면 디스크 한계때문에 서버 멈출수도 있으므로 로그 보존 정책으로 디스크를 관리해야함.
```
crontab 표현식 의미:
* * * * * 명령어
│ │ │ │ │
│ │ │ │ └── 요일 (0-7)
│ │ │ └──── 월 (1-12)
│ │ └────── 일 (1-31)
│ └──────── 시 (0-23)
└────────── 분 (0-
```


---

## 리다이렉션 설명

```text
> 는 기존 파일 내용을 덮어쓴다(overwrite).
>> 는 기존 내용을 유지하면서 append한다.

monitor.log는 시간 순서대로 상태를 누적 기록해야 하므로,
기존 로그를 유지하는 >> append 방식이 필요하다.
```

---

# 6. monitor.sh 설계 및 명령 선택 이유

## 프로세스 확인 방식

```text
pgrep -f를 사용한 이유는 실행 중인 프로세스의 전체 command line 기준 검색이 가능하기 때문이다.

단순 ps | grep 방식보다 불필요한 grep 프로세스 매칭 위험이 적고,
자동화 스크립트에 적합하다.
```

---

## 포트 확인 방식

```text
ss 명령은 Linux socket 상태를 직접 조회할 수 있으며 LISTEN 상태 확인이 가능하다.

netstat보다 최신 Linux 환경에서 권장되는 도구이므로 ss를 선택하였다.
```

---

## CPU / MEM / DISK 파싱 방식

```text
CPU 사용률은 top -bn1 결과에서 idle 값을 제외하는 방식으로 계산하였다.

메모리 사용률은 free 명령 결과에서 used/total 비율을 계산하였다.

디스크 사용률은 df / 결과에서 root partition 사용률만 추출하였다.
```

---

## 로그 포맷 고정 이유

```text
로그 포맷은 timestamp + PID + resource metric 구조로 고정하였다.

이는 운영 환경에서 시간 기준 장애 추적과 grep/awk 기반 후처리를 쉽게 하기 위함이다.
```

---

# 7. 로그 용량 관리

## 로그 로테이션 정책

```text
monitor.log 파일 크기가 10MB를 초과하면:
- 기존 로그 파일을 monitor.log.1 ~ monitor.log.10 형태로 순차 이동
- 최신 로그는 새 monitor.log에 기록
- 최대 10개 로그 파일 유지
정책을 적용하였다.
```

### 로그 관리 중요성

```text
운영 환경에서는 로그 폭증으로 인해 디스크가 가득 차면 서비스 장애로 이어질 수 있다.

따라서:
- 로그 압축
- 오래된 로그 삭제
- 보존 정책 관리
등이 중요하다.
```

---

# 8. 운영 확장 및 장애 대응

## 웹 서버(Nginx)로 변경될 경우

```text
모니터링 대상이 Nginx로 변경된다면:
- 프로세스명(agent_app.py → nginx)
- 포트(15034 → 80/443)
- 로그 경로(access/error log)
- 임계값 기준
등을 변경해야 한다.

또한 HTTP 상태 코드(5xx 비율)나 worker process 상태도 추가 모니터링 대상이 될 수 있다.
```

---

## 프로세스는 살아있지만 포트가 안 열리는 경우

```text
가능한 원인:
1. bind 실패
2. 포트 충돌
3. 방화벽 차단
4. 권한 문제
5. 애플리케이션 내부 deadlock
6. startup incomplete

확인 순서:
1. ss -tulnp 로 LISTEN 상태 확인
2. application log 확인
3. ps/pgrep 로 process 상태 확인
4. journalctl/system log 확인
5. firewall(UFW) 상태 확인
```

---

## 로그 급증 대응


* 단기 대응:
```text
- 불필요 로그 제거
- logrotate 강제 수행
- 오래된 로그 압축/삭제
- 디스크 사용량 확인
```

* 중기 대응:
```text
- 로그 레벨 조정
- 중앙 로그 수집 시스템 구축
- 보존 정책 수립
- 모니터링/알림 연동
```