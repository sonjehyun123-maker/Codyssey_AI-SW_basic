import argparse
import sys
from typing import List

from .decorators import handle_errors, log_execution, measure_time
from .models import Transaction
from .service import BudgetService


def format_tx(tx: Transaction) -> str:
    type_col = tx.type.ljust(7)
    parts = [tx.id, tx.date, type_col, tx.category, str(tx.amount), tx.memo]
    return " | ".join(parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app", description="콘솔 가계부")
    parser.add_argument("--data-dir", default="./data", help="데이터 저장 폴더 (기본값: ./data)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("add", help="대화형으로 거래 추가")

    p_list = sub.add_parser("list", help="거래 목록 조회 (최신순)")
    p_list.add_argument("--limit", type=int, default=10)

    p_search = sub.add_parser("search", help="조건 기반 거래 검색")
    p_search.add_argument("--from", dest="date_from")
    p_search.add_argument("--to", dest="date_to")
    p_search.add_argument("--category")
    p_search.add_argument("--type", dest="type_", choices=["income", "expense"])
    p_search.add_argument("--q")
    p_search.add_argument("--tag")

    p_summary = sub.add_parser("summary", help="월별 요약")
    p_summary.add_argument("--month", required=True)
    p_summary.add_argument("--top", type=int, default=3)

    p_budget = sub.add_parser("budget", help="예산 설정")
    budget_sub = p_budget.add_subparsers(dest="budget_command", required=True)
    p_budget_set = budget_sub.add_parser("set", help="월 예산 설정")
    p_budget_set.add_argument("--month", required=True)
    p_budget_set.add_argument("--amount", required=True)

    p_category = sub.add_parser("category", help="카테고리 관리")
    cat_sub = p_category.add_subparsers(dest="category_command", required=True)
    cat_sub.add_parser("add", help="대화형으로 카테고리 추가")
    cat_sub.add_parser("list", help="카테고리 목록")
    p_cat_remove = cat_sub.add_parser("remove", help="카테고리 삭제")
    p_cat_remove.add_argument("--name", required=True)
    p_cat_remove.add_argument("--replace-with")

    p_update = sub.add_parser("update", help="옵션 기반 거래 수정")
    p_update.add_argument("--id", required=True)
    p_update.add_argument("--date")
    p_update.add_argument("--type", dest="type_", choices=["income", "expense"])
    p_update.add_argument("--category")
    p_update.add_argument("--amount")
    p_update.add_argument("--memo")
    p_update.add_argument("--tags")

    p_delete = sub.add_parser("delete", help="거래 삭제")
    p_delete.add_argument("--id", required=True)

    p_export = sub.add_parser("export", help="CSV로 내보내기")
    p_export.add_argument("--out", required=True)
    p_export.add_argument("--month")
    p_export.add_argument("--from", dest="date_from")
    p_export.add_argument("--to", dest="date_to")

    p_import = sub.add_parser("import", help="CSV에서 가져오기")
    p_import.add_argument("--from", dest="in_path", required=True)

    return parser


@handle_errors
@log_execution
@measure_time
def cmd_add(service: BudgetService, args: argparse.Namespace) -> None:
    date = input("날짜(YYYY-MM-DD): ").strip()
    type_ = input("타입(income/expense): ").strip()
    category = input("카테고리: ").strip()
    amount = input("금액(양수): ").strip()
    memo = input("메모(선택): ").strip()
    tags_raw = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
    tx = service.add_transaction(date, type_, category, amount, memo, tags)
    print(f"[저장 완료] id={tx.id}")


@handle_errors
def cmd_list(service: BudgetService, args: argparse.Namespace) -> None:
    for tx in service.list_transactions(args.limit):
        print(format_tx(tx))


@handle_errors
def cmd_search(service: BudgetService, args: argparse.Namespace) -> None:
    results = service.search_transactions(
        date_from=args.date_from, date_to=args.date_to, category=args.category,
        type_=args.type_, q=args.q, tag=args.tag,
    )
    if not results:
        print("검색 결과가 없습니다.")
        return
    for tx in results:
        print(format_tx(tx))


@handle_errors
@measure_time
def cmd_summary(service: BudgetService, args: argparse.Namespace) -> None:
    result = service.summary(args.month, args.top)
    if not result["found"]:
        print("데이터 없음")
        return
    print(f"총 수입: {result['income']}원")
    print(f"총 지출: {result['expense']}원")
    print(f"잔액: {result['balance']}원")
    if result["budget"] is not None:
        print(f"예산: {result['budget']}원 (사용률 {result['usage_rate']:.1f}%)")
        if result["over_budget"]:
            print("[경고] 예산을 초과했습니다!")
    print()
    print(f"지출 TOP {args.top}")
    for i, (category, amount) in enumerate(result["top_categories"], start=1):
        print(f"{i}) {category} {amount}원")


@handle_errors
def cmd_budget_set(service: BudgetService, args: argparse.Namespace) -> None:
    amount = service.set_budget(args.month, args.amount)
    print(f"[저장 완료] {args.month} 예산 {amount}원")


@handle_errors
def cmd_category_add(service: BudgetService, args: argparse.Namespace) -> None:
    name = input("카테고리명: ").strip()
    service.category_add(name)
    print(f"[저장 완료] category={name}")


@handle_errors
def cmd_category_list(service: BudgetService, args: argparse.Namespace) -> None:
    for name in service.category_list():
        print(f"- {name}")


@handle_errors
def cmd_category_remove(service: BudgetService, args: argparse.Namespace) -> None:
    service.category_remove(args.name, args.replace_with)
    print(f"[삭제 완료] category={args.name}")


@handle_errors
def cmd_update(service: BudgetService, args: argparse.Namespace) -> None:
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags is not None else None
    tx = service.update_transaction(
        args.id, date=args.date, type=args.type_, category=args.category,
        amount=args.amount, memo=args.memo, tags=tags,
    )
    print(f"[수정 완료] id={tx.id}")


@handle_errors
def cmd_delete(service: BudgetService, args: argparse.Namespace) -> None:
    service.delete_transaction(args.id)
    print(f"[삭제 완료] id={args.id}")


@handle_errors
def cmd_export(service: BudgetService, args: argparse.Namespace) -> None:
    count = service.export_csv(args.out, month=args.month, date_from=args.date_from, date_to=args.date_to)
    print(f"[완료] {args.out} ({count} records)")


@handle_errors
def cmd_import(service: BudgetService, args: argparse.Namespace) -> None:
    imported, skipped = service.import_csv(args.in_path)
    print(f"[완료] imported={imported}, skipped={skipped}")


def main(argv: List[str] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = BudgetService(args.data_dir)

    if args.command == "add":
        cmd_add(service, args)
    elif args.command == "list":
        cmd_list(service, args)
    elif args.command == "search":
        cmd_search(service, args)
    elif args.command == "summary":
        cmd_summary(service, args)
    elif args.command == "budget":
        cmd_budget_set(service, args)
    elif args.command == "category":
        if args.category_command == "add":
            cmd_category_add(service, args)
        elif args.category_command == "list":
            cmd_category_list(service, args)
        elif args.category_command == "remove":
            cmd_category_remove(service, args)
    elif args.command == "update":
        cmd_update(service, args)
    elif args.command == "delete":
        cmd_delete(service, args)
    elif args.command == "export":
        cmd_export(service, args)
    elif args.command == "import":
        cmd_import(service, args)

    sys.exit(0)
