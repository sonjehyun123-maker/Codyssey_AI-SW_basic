import argparse

from collector import get_git_status, get_git_diff, get_current_branch
from prompt_builder import build_commit_prompt, build_pr_prompt
from api_caller import generate_with_retry
from formatter import (
    validate_commit_format,
    validate_pr_format,
    parse_pr_result,
    print_commit_result,
    print_pr_result,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        add_help=False
    )

    parser.add_argument(
        "-h", "--help", "-help",
        action="help",
        help="사용법을 출력합니다."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-m", "--model",
        dest="model",
        default="gemini-3.5-flash"
    )
    common.add_argument(
        "-t", "--temperature",
        dest="temperature",
        type=float,
        default=0.7
    )
    common.add_argument(
        "-mt", "--max-tokens",
        dest="max_tokens",
        type=int,
        default=5120
    )
    common.add_argument(
        "-s", "--safe-mode",
        dest="safe_mode",
        action="store_true"
    )

    subparsers.add_parser("commit", parents=[common])
    subparsers.add_parser("pr", parents=[common])

    return parser


def run_commit(args):
    status = get_git_status()
    diff = get_git_diff()
    if not diff.strip():
        print("[INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다.")
        return

    print(f"[INFO] Git status 수집 완료")
    print(f"[INFO] Git diff 수집 완료: {len(diff.splitlines())}줄")

    prompt = build_commit_prompt(status, diff, args.safe_mode)
    result = generate_with_retry(prompt, validate_commit_format, args)

    if result is None:
        return

    print("[DONE] 커밋 메시지 생성 완료")
    print_commit_result(result)


def run_pr(args):
    status = get_git_status()
    diff = get_git_diff()
    if not diff.strip():
        print("[INFO] 변경 사항이 없습니다. PR을 생성하지 않고 종료합니다.")
        return

    branch = get_current_branch()
    print(f"[INFO] 현재 브랜치: {branch}")

    prompt = build_pr_prompt(status, diff, branch, args.safe_mode)
    result = generate_with_retry(prompt, validate_pr_format, args)

    if result is None:
        return

    print("[DONE] PR 초안 생성 완료")
    title, body = parse_pr_result(result)
    print_pr_result(title, body)


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "commit":
        run_commit(args)
    elif args.command == "pr":
        run_pr(args)


if __name__ == "__main__":
    main()