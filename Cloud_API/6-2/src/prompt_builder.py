import re


def mask_sensitive(diff_text: str) -> str:
    diff_text = re.sub(r'[A-Za-z0-9_\-]{20,}', '[MASKED_KEY]', diff_text)
    diff_text = re.sub(r'[\w.+-]+@[\w-]+\.\w+', '[MASKED_EMAIL]', diff_text)
    return diff_text


def build_commit_prompt(status: str, diff: str, safe_mode: bool) -> str:
    if safe_mode:
        diff = mask_sensitive(diff)

    return f"""다음 git 변경사항을 보고 커밋 메시지를 작성해줘.

[규칙]
- 제목은 50자 이내 권장, 최대 72자 절대 초과 금지
- 본문은 변경 파일 1~3개 언급 + 핵심 변경 불릿 1~2개 포함 (선택)
- 제목과 본문 사이는 빈 줄 하나로 구분

[status]
{status}

[diff]
{diff}
"""


def build_pr_prompt(status: str, diff: str, branch_name: str, safe_mode: bool) -> str:
    if safe_mode:
        diff = mask_sensitive(diff)

    return f"""다음 git 변경사항을 보고 Pull Request 제목과 본문을 작성해줘.

[출력 형식 - 반드시 이 형식을 그대로 지켜라]
PR_TITLE: <제목 1줄, 80자 이내>
PR_BODY:
## Why
- <배경 불릿 최소 1개>
## What
- <핵심 변경사항 불릿 최소 1개, 여러 개 가능>
## How to Test
- <테스트 방법 불릿 최소 1개>

[규칙]
- PR_TITLE은 한 줄로만 작성, 접두어(feat/fix 등) 포함, 80자 절대 초과 금지
- 각 섹션(##)은 반드시 포함, 섹션 제목을 임의로 바꾸지 마라
- 각 섹션은 불릿(-)으로 작성하고 최소 1개 이상
- 코드 설명이 아니라 변경 의도와 영향 중심으로 작성

[브랜치명]
{branch_name}

[status]
{status}

[diff]
{diff}
"""
