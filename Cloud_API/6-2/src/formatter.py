import re


def validate_commit_format(text: str) -> bool:
    lines = text.strip().split("\n")
    if not lines or not lines[0].strip():
        return False
    title = lines[0].strip()
    if len(title) > 72:
        return False
    return True


def validate_pr_format(text: str) -> bool:
    if "PR_TITLE:" not in text or "PR_BODY:" not in text:
        return False

    title_match = re.search(r"PR_TITLE:\s*(.+)", text)
    if not title_match or len(title_match.group(1).strip()) > 80:
        return False

    for header in ["## Why", "## What", "## How to Test"]:
        if header not in text:
            return False
        section = text.split(header, 1)[1].split("##")[0]
        if "-" not in section:
            return False

    return True


def parse_pr_result(text: str) -> tuple[str, str]:
    title = re.search(r"PR_TITLE:\s*(.+)", text).group(1).strip()
    body = text.split("PR_BODY:", 1)[1].strip()
    return title, body


def print_commit_result(text: str):
    print("--- Commit Message ---")
    print(text.strip())
    print("----------------------")


def print_pr_result(title: str, body: str):
    print("--- PR Title ---")
    print(title)
    print("--- PR Body ---")
    print(body)
