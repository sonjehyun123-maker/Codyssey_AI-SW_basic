import os
import sys
import subprocess
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prompt_builder import mask_sensitive, build_commit_prompt
from formatter import validate_commit_format, validate_pr_format, parse_pr_result

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(TEST_DIR)
FIXTURES_PATH = os.path.join(TEST_DIR, "fixtures.txt")


def load_fixtures() -> tuple[str, str]:
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    sensitive = content.split("### SENSITIVE ###", 1)[1].split("### NORMAL ###", 1)[0].strip("\n")
    normal = content.split("### NORMAL ###", 1)[1].strip("\n")
    return sensitive, normal


def check(name, condition) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def run_unit_tests(sensitive_content: str) -> bool:
    print("===== 1. 유닛 테스트 (마스킹 / 검증 / 파싱, API 호출 없음) =====")
    results = []

    masked = mask_sensitive(sensitive_content)
    results.append(check("Google API Key 마스킹", "AIzaSyDaGmWKa4JsXZ" not in masked))
    results.append(check("GitHub Token 마스킹", "ghp_1234567890" not in masked))
    results.append(check("AWS Access Key 마스킹", "AKIAIOSFODNN7EXAMPLE" not in masked))
    results.append(check("다단계 도메인 이메일(ADMIN_EMAIL) 완전 마스킹", "anyang.ac.kr" not in masked))
    results.append(check("일반 도메인 이메일(SUPPORT_EMAIL) 완전 마스킹", "codyssey-helper.com" not in masked))
    results.append(check("설명 주석은 그대로 유지됨", "결제 모듈 환경설정" in masked))

    prompt_on = build_commit_prompt("M app.py", sensitive_content, safe_mode=True)
    results.append(check("safe_mode=True시 원본 미노출", "AIzaSyDaGmWKa4JsXZ" not in prompt_on))

    prompt_off = build_commit_prompt("M app.py", sensitive_content, safe_mode=False)
    results.append(check("safe_mode=False시 원본 그대로 전달", "AIzaSyDaGmWKa4JsXZ" in prompt_off))

    results.append(check("commit 검증: 정상 케이스 통과", validate_commit_format("feat: 로그인 기능 추가")))
    results.append(check("commit 검증: 72자 초과 실패", not validate_commit_format("a" * 100)))

    good_pr = (
        "PR_TITLE: feat: 테스트\n"
        "PR_BODY:\n## Why\n- 배경\n## What\n- 변경\n## How to Test\n- 방법\n"
    )
    results.append(check("pr 검증: 정상 케이스 통과", validate_pr_format(good_pr)))
    results.append(check("pr 검증: 헤더 누락 실패", not validate_pr_format("PR_TITLE: 제목\nPR_BODY:\n내용만")))

    title, _ = parse_pr_result(good_pr)
    results.append(check("pr 파싱: 제목 추출 정확도", title == "feat: 테스트"))

    print(f"\n유닛 테스트 {sum(results)}/{len(results)} 통과\n")
    return all(results)


def run_cli_scenario(title: str, change_content: str, extra_args: list[str]):
    print(f"===== {title} =====")
    scratch = tempfile.mkdtemp(prefix="git_ai_helper_test_")
    try:
        subprocess.run(["git", "init", "-q"], cwd=scratch, check=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=scratch, check=True)
        subprocess.run(["git", "config", "user.name", "test"], cwd=scratch, check=True)

        app_path = os.path.join(scratch, "app.py")
        with open(app_path, "w") as f:
            f.write("# base file\n")
        subprocess.run(["git", "add", "."], cwd=scratch, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=scratch, check=True)

        with open(app_path, "a") as f:
            f.write(change_content)

        diff_result = subprocess.run(["git", "diff"], cwd=scratch, capture_output=True, text=True)
        original_diff = diff_result.stdout
        print("--- git diff (원본) ---")
        print(original_diff)

        if "-safe-mode" in extra_args:
            masked_diff = mask_sensitive(original_diff)
            print("--- diff 마스킹 후 (safe-mode 적용, 실제 AI로 전송되는 형태) ---")
            print(masked_diff)

        for cmd in ["commit", "pr"]:
            print(f"--- python3 main.py {cmd} {' '.join(extra_args)} ---".strip())
            result = subprocess.run(
                [sys.executable, os.path.join(SRC_DIR, "main.py"), cmd, *extra_args],
                cwd=scratch, capture_output=True, text=True
            )
            print(result.stdout.strip())
            if result.stderr.strip():
                print(result.stderr.strip())
            print()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main():
    sensitive_content, normal_content = load_fixtures()

    unit_ok = run_unit_tests(sensitive_content)
    run_cli_scenario("2. 민감정보 포함 케이스 (safe-mode 사용)", sensitive_content, ["-safe-mode"])
    run_cli_scenario("3. 일반 케이스 (safe-mode 미사용)", normal_content, [])

    if not unit_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()