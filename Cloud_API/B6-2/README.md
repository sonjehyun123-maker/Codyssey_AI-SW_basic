# Git AI Helper

`git status`/`git diff` 결과를 AI API에 넘겨 커밋 메시지와 PR 초안을 자동 생성하는 CLI 도구입니다. 다른 프로젝트들이 CS 개념 구현에 집중했다면, 이 프로젝트는 **실제 개발 도구를 만드는 능력**과 **AI 응답을 신뢰하지 않고 검증하는 파이프라인 설계**에 초점을 맞췄습니다.

---

## 1. Overview

```
$ python main.py commit
[INFO] Git status 수집 완료
[INFO] Git diff 수집 완료: 7줄
[INFO] AI API 요청 중... (시도 1/1)
[DONE] 커밋 메시지 생성 완료
--- Commit Message ---
feat: 커밋/PR 자동 생성 기능 추가

- collector.py, api_caller.py 신규 작성
- git diff 결과를 AI 입력 컨텍스트로 전달하도록 구현
----------------------
```

커밋 메시지·PR 설명 작성 자체보다 **"무슨 내용을 어떤 형식으로 담을지 정리하는 시간"**이 더 오래 걸린다는 문제에서 출발했습니다. Gemini API를 호출해 diff로부터 커밋 메시지와 `Why/What/How to Test` 구조의 PR 초안을 생성합니다.

## 2. Problem

AI에게 텍스트 생성을 맡기는 건 쉽지만, 그 결과를 **그대로 신뢰할 수 없다**는 게 실제 문제였습니다.

- AI가 매번 다른 형식으로 응답하면 자동화 도구로서 쓸모가 없다 → **출력 형식을 어떻게 강제할 것인가**
- diff에는 API Key, 이메일 같은 민감정보가 섞여 들어갈 수 있다 → **AI에게 보내기 전에 어떻게 걸러낼 것인가**
- API 호출은 비용이 들고 실패할 수 있다 → **무한 재시도 없이, 그러나 일시적 실패는 복구 가능하게 어떻게 설계할 것인가**

즉 핵심은 "AI API를 호출하는 코드"가 아니라, **비정형 텍스트(diff)를 신뢰 가능한 정형 데이터(커밋/PR 스키마)로 강제 변환하는 파이프라인**을 만드는 것이었습니다.

## 3. Architecture

```
collector.py        # git status/diff/branch 수집 (subprocess)
prompt_builder.py    # safe-mode 마스킹 + 프롬프트 조립
api_caller.py         # Gemini REST 호출 + 재시도
formatter.py          # 출력 형식 검증 + 파싱 + 출력
main.py               # 위 4단계를 순서대로 오케스트레이션
```

**PR 생성 흐름**

```
git status / diff 실행
  → Collector: 결과를 문자열로 수집
  → Prompt Builder: safe-mode 마스킹 + 프롬프트 조립 (PR_TITLE:/PR_BODY: 프리픽스 강제)
  → API Caller: Gemini REST 호출
  → Formatter: 헤더(## Why/What/How to Test) + 불릿 존재 여부 검증
       실패 → API Caller로 재시도 (MAX_RETRIES = 1)
       통과 → 터미널 출력
       재시도 후에도 실패 → 에러 메시지 출력
```

변경사항이 없으면 Collector 단계에서 바로 종료되고, 재시도는 실행당 최대 1회로 제한됩니다(API 비용 제약).

## 4. Core Concepts

| 개념 | 적용 위치 | 핵심 |
|---|---|---|
| 레이어 분리 | 전체 구조 | Collector(수집) / Prompt Builder(조립) / API Caller(호출) / Formatter(검증)로 책임 분리, `main.py`는 순서만 담당 |
| 정규식 기반 민감정보 마스킹 | `prompt_builder.py :: mask_sensitive()` | 20자 이상 + 숫자 포함 문자열(Key/Token 패턴) + 이메일 패턴을 치환 |
| 검증 함수 주입(전략 패턴) | `api_caller.py :: generate_with_retry()` | commit/PR의 검증 기준은 다르지만 재시도 로직은 동일 — `validate_fn`을 인자로 받아 코드 중복 제거 |
| 실패 유형 분리 | `api_caller.py` | 인증 실패(재시도 무의미, 즉시 반환) vs 형식 검증 실패(재시도 유의미)를 다른 경로로 처리 |
| 재시도 vs 후처리 | `formatter.py` | 형식 미달 텍스트를 "잘라내기"보다 "재생성"을 택함 — 자르면 문장이 어색하게 끊기는 문제 회피 |

## 5. Implementation

**민감정보 마스킹 — 숫자 포함 여부로 오탐 줄이기**
```python
# 20자 이상 + 숫자 포함 → Key/Token 패턴으로 간주
# 순수 문자로만 이루어진 긴 함수명(예: connect_external_api)은 제외
def mask_sensitive(diff_text: str) -> str:
    ...
```
길이 조건만 두면 `connect_external_api` 같은 일반 함수명·변수명까지 API Key로 오인해 마스킹되는 문제가 있어, **숫자 포함 여부**를 추가 조건으로 넣어 오탐을 줄였습니다.

**검증 함수 주입 — 재시도 로직 재사용**
```python
def generate_with_retry(prompt: str, validate_fn, args) -> str | None:
    # commit: 제목 길이만 검증
    # PR: 헤더 + 섹션 내 불릿 존재까지 검증
    # → 검증 기준이 달라도 재시도 로직 자체(호출→검증→재시도)는 하나로 재사용
```

**PR 형식 검증 — 헤더뿐 아니라 내용까지**
```python
def validate_pr_format(text: str) -> bool:
    # "## Why", "## What", "## How to Test" 헤더 존재 확인
    # 각 섹션 안에 "-" 불릿이 최소 1개 있는지까지 확인
    # → 헤더만 확인하면 "내용 없는 빈 섹션"도 통과되는 허점을 막음
```

## 6. Design Decisions

**왜 인증 체크를 `api_caller.py` 내부에 뒀는가?**
"인증은 API 호출의 책임"이라는 레이어 분리 원칙에 따라, `main.py`가 인증 로직을 전혀 몰라도 되게 만들었습니다. 이 덕분에 `main.py`는 순서 조립에만 집중할 수 있습니다.

**왜 검증 실패 시 텍스트를 자르지 않고 재생성하는가?**
길이나 형식이 안 맞는 부분을 후처리로 잘라내면 문장이 어색하게 끊기는 문제가 생깁니다. 대신 "형식을 안 지켰으면 다시 생성한다"는 원칙을 세우고, 프롬프트에서 형식을 명시(1차 방어선) + Formatter가 최종 판단(2차 방어선)하는 이중 구조로 품질을 담보했습니다.

**왜 재시도를 최대 1회로 제한했는가?**
과제 제약(실행당 API 호출 1~2회 이내 권장)과 Gemini 무료 티어 범위를 고려한 결정입니다. 무한 재시도는 실패 원인이 형식 문제가 아니라 API 자체 문제일 때 비용만 낭비하게 됩니다.

**왜 `PR_TITLE:`/`PR_BODY:` 프리픽스를 프롬프트에 강제했는가?**
Formatter에서 정규식 하나로 제목과 본문을 분리할 수 있게 하기 위한 설계입니다. 파싱 편의를 프롬프트 설계 단계에서 미리 고려한 것으로, "AI 출력을 어떻게 파싱할지"를 프롬프트 작성 시점부터 함께 설계했습니다.

## 7. Testing

`make test` 한 명령으로 유닛 테스트부터 실제 시나리오까지 검증합니다.

| 항목 | 내용 |
|---|---|
| 유닛 테스트 | 마스킹/검증/파싱 로직 — API 호출 없이 13개 케이스 |
| 민감정보 케이스 | `test/fixtures.txt`의 `### SENSITIVE ###` 구간을 임시 Git 저장소에 적용, `-safe-mode`로 실행. 마스킹 전/후를 로그에 함께 남겨 비교 가능 |
| 일반 케이스 | `### NORMAL ###` 구간으로 safe-mode 없이 실행 |

```
Makefile          → make test 진입점
test/run_tests.sh → 로그 생성 + run_tests.py 실행
test/run_tests.py → 유닛 테스트 + 임시 git 저장소 생성 시나리오
test/fixtures.txt → SENSITIVE/NORMAL 케이스를 마커로 구분한 단일 파일
```

임시 저장소는 실행마다 새로 생성/자동 삭제되고, 전체 로그는 `logs/test_<타임스탬프>.log`에 저장됩니다.

## 8. Result

```
$ python main.py pr
[INFO] 현재 브랜치: feature/commit-pr-generator
[INFO] AI API 요청 중... (시도 1/1)
[DONE] PR 초안 생성 완료
--- PR Title ---
feat: 커밋/PR 자동 생성 기능 추가
--- PR Body ---
## Why
- 커밋 메시지와 PR 설명 작성에 반복적으로 시간이 소요되어 자동화가 필요했습니다.

## What
- git status/diff 수집 후 AI 입력으로 전달하는 로직 추가
- commit/pr 명령어 및 형식 검증 로직 구현

## How to Test
- export GEMINI_API_KEY="YOUR_KEY" 설정 후 python main.py pr 실행
```

`GEMINI_API_KEY` 미설정 시에는 재시도 없이 즉시 에러를 안내하고, 변경사항이 없을 때는 API 호출 자체를 하지 않고 조기 종료합니다.

## 9. What I Learned

- AI API를 호출하는 코드 자체는 몇 줄이면 끝나지만, **"신뢰할 수 있는 도구"로 만드는 건 검증·재시도·실패 분리 설계**라는 것을 체감했습니다.
- 검증 함수를 인자로 주입하는 패턴(전략 패턴)이 "본질적으로 같은 흐름, 세부 기준만 다른" 상황에서 코드 중복을 줄이는 데 효과적이라는 것.
- 정규식 기반 마스킹처럼 휴리스틱에 의존하는 방법은 **완벽한 탐지를 보장할 수 없다는 한계**를 명확히 인지하고 문서화하는 것도 설계의 일부라는 것.
- 실패를 하나로 뭉뚱그리지 않고 "재시도해도 되는 실패"와 "재시도가 무의미한 실패"를 구분하는 게 비용과 사용자 경험 모두에 중요하다는 것.

## 10. Future Improvements

- GitHub Actions 연동 — PR 생성 시 자동으로 이 도구를 실행해 초안을 코멘트로 남기는 워크플로우
- 마스킹 로직의 오탐/누락 사례를 더 모아 정규식 규칙 정교화 (현재는 완벽한 탐지를 보장하지 않음을 명시)
- 커밋 메시지 스타일을 프로젝트별 컨벤션(Conventional Commits 등)에 맞게 설정 가능하도록 확장
- 다른 AI 모델(Claude, GPT 등) 백엔드 선택 옵션 추가