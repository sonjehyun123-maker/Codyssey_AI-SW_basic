import csv
import os
from collections import deque
from datetime import datetime
from typing import List, Optional

from .decorators import AppError
from .models import Transaction
from .storage import BudgetStore, CategoryStore, TransactionRepository

DEFAULT_CATEGORIES = ["food", "transport", "rent", "etc"]
CSV_FIELDS = ["date", "type", "category", "amount", "memo", "tags"]


def validate_date(date_str: str) -> None:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise AppError("날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", "예: 2024-01-15")


def validate_type(type_str: str) -> None:
    if type_str not in ("income", "expense"):
        raise AppError("type은 income 또는 expense만 가능합니다.", "예: expense")


def validate_amount(amount_str: str) -> int:
    try:
        amount = int(amount_str)
    except ValueError:
        raise AppError("금액은 숫자여야 합니다.", "예: 15000")
    if amount <= 0:
        raise AppError("금액은 양수여야 합니다.", "예: 15000")
    return amount


class BudgetService:
    def __init__(self, data_dir: str):
        os.makedirs(data_dir, exist_ok=True)
        is_new = not os.path.exists(os.path.join(data_dir, "transactions.jsonl"))
        self.tx_repo = TransactionRepository(os.path.join(data_dir, "transactions.jsonl"))
        self.cat_store = CategoryStore(os.path.join(data_dir, "categories.jsonl"))
        self.budget_store = BudgetStore(os.path.join(data_dir, "budgets.jsonl"))
        if is_new:
            print(f"[초기화] 데이터 폴더 생성: {data_dir}")
        if not self.cat_store.list_all():
            for c in DEFAULT_CATEGORIES:
                self.cat_store.add(c)
            print(f"[초기화] 기본 카테고리 생성: {', '.join(DEFAULT_CATEGORIES)}")

    def _require_category(self, category: str) -> None:
        if category not in self.cat_store.list_all():
            raise AppError(
                f"등록되지 않은 카테고리입니다: {category}",
                "category add 로 먼저 등록해 주세요.",
            )

    def add_transaction(
        self, date: str, type_: str, category: str, amount_str: str,
        memo: str = "", tags: Optional[List[str]] = None,
    ) -> Transaction:
        validate_date(date)
        validate_type(type_)
        amount = validate_amount(amount_str)
        self._require_category(category)
        tx = Transaction(
            id=self.tx_repo.next_id(), type=type_, date=date, amount=amount,
            category=category, memo=memo, tags=tags or [],
        )
        self.tx_repo.append(tx)
        return tx

    def list_transactions(self, limit: int) -> List[Transaction]:
        buffer: deque = deque(maxlen=limit)
        for tx in self.tx_repo.stream_all():
            buffer.append(tx)
        return list(reversed(buffer))

    def search_transactions(
        self, date_from: Optional[str] = None, date_to: Optional[str] = None,
        category: Optional[str] = None, type_: Optional[str] = None,
        q: Optional[str] = None, tag: Optional[str] = None,
    ) -> List[Transaction]:
        results = []
        for tx in self.tx_repo.stream_all():
            if date_from and tx.date < date_from:
                continue
            if date_to and tx.date > date_to:
                continue
            if category and tx.category != category:
                continue
            if type_ and tx.type != type_:
                continue
            if q and q.lower() not in tx.memo.lower():
                continue
            if tag and tag not in tx.tags:
                continue
            results.append(tx)
        results.sort(key=lambda t: (t.date, t.id), reverse=True)
        return results

    def summary(self, month: str, top: int = 3) -> dict:
        income = expense = 0
        by_category: dict = {}
        found = False
        for tx in self.tx_repo.stream_all():
            if not tx.date.startswith(month):
                continue
            found = True
            if tx.type == "income":
                income += tx.amount
            else:
                expense += tx.amount
                by_category[tx.category] = by_category.get(tx.category, 0) + tx.amount
        top_categories = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)[:top]
        budget_amount = self.budget_store.get(month)
        result = {
            "found": found, "income": income, "expense": expense,
            "balance": income - expense, "top_categories": top_categories,
            "budget": budget_amount,
        }
        if budget_amount:
            usage_rate = expense / budget_amount * 100
            result["usage_rate"] = usage_rate
            result["over_budget"] = expense > budget_amount
        return result

    def set_budget(self, month: str, amount_str: str) -> int:
        amount = validate_amount(amount_str)
        self.budget_store.set(month, amount)
        return amount

    def category_add(self, name: str) -> None:
        if name in self.cat_store.list_all():
            raise AppError(f"이미 존재하는 카테고리입니다: {name}")
        self.cat_store.add(name)

    def category_list(self) -> List[str]:
        return self.cat_store.list_all()

    def category_remove(self, name: str, replace_with: Optional[str] = None) -> None:
        if name not in self.cat_store.list_all():
            raise AppError(f"존재하지 않는 카테고리입니다: {name}")
        in_use = [tx for tx in self.tx_repo.stream_all() if tx.category == name]
        if in_use:
            if not replace_with:
                raise AppError(
                    f"'{name}' 카테고리를 사용 중인 내역이 {len(in_use)}건 있습니다.",
                    "--replace-with <대체 카테고리> 옵션을 지정해 주세요.",
                )
            self._require_category(replace_with)
            all_tx = list(self.tx_repo.stream_all())
            for tx in all_tx:
                if tx.category == name:
                    tx.category = replace_with
            self.tx_repo.rewrite_all(all_tx)
        self.cat_store.remove(name)

    def update_transaction(self, tx_id: str, **fields) -> Transaction:
        all_tx = list(self.tx_repo.stream_all())
        target = next((t for t in all_tx if t.id == tx_id), None)
        if target is None:
            raise AppError(f"존재하지 않는 id입니다: {tx_id}")
        if fields.get("date") is not None:
            validate_date(fields["date"])
            target.date = fields["date"]
        if fields.get("type") is not None:
            validate_type(fields["type"])
            target.type = fields["type"]
        if fields.get("category") is not None:
            self._require_category(fields["category"])
            target.category = fields["category"]
        if fields.get("amount") is not None:
            target.amount = validate_amount(fields["amount"])
        if fields.get("memo") is not None:
            target.memo = fields["memo"]
        if fields.get("tags") is not None:
            target.tags = fields["tags"]
        self.tx_repo.rewrite_all(all_tx)
        return target

    def delete_transaction(self, tx_id: str) -> None:
        all_tx = list(self.tx_repo.stream_all())
        remaining = [t for t in all_tx if t.id != tx_id]
        if len(remaining) == len(all_tx):
            raise AppError(f"존재하지 않는 id입니다: {tx_id}")
        self.tx_repo.rewrite_all(remaining)

    def export_csv(
        self, out_path: str, month: Optional[str] = None,
        date_from: Optional[str] = None, date_to: Optional[str] = None,
    ) -> int:
        if not month and not (date_from and date_to):
            raise AppError(
                "export 조건이 필요합니다.",
                "--month YYYY-MM 또는 --from/--to 를 지정해 주세요.",
            )
        rows = []
        for tx in self.tx_repo.stream_all():
            if month and not tx.date.startswith(month):
                continue
            if date_from and tx.date < date_from:
                continue
            if date_to and tx.date > date_to:
                continue
            rows.append(tx)
        rows.sort(key=lambda t: t.date)
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for tx in rows:
                writer.writerow({
                    "date": tx.date, "type": tx.type, "category": tx.category,
                    "amount": tx.amount, "memo": tx.memo, "tags": ",".join(tx.tags),
                })
        return len(rows)

    def import_csv(self, in_path: str) -> "tuple[int, int]":
        imported = skipped = 0
        next_num = int(self.tx_repo.next_id().split("-")[1])
        with open(in_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = row["date"].strip()
                    type_ = row["type"].strip()
                    category = row["category"].strip()
                    validate_date(date)
                    validate_type(type_)
                    amount = validate_amount(row["amount"])
                    self._require_category(category)
                    memo = (row.get("memo") or "").strip()
                    tags_raw = (row.get("tags") or "").strip()
                    tags = [t for t in tags_raw.split(",") if t] if tags_raw else []
                    tx = Transaction(
                        id=f"TX-{next_num:06d}", type=type_, date=date,
                        amount=amount, category=category, memo=memo, tags=tags,
                    )
                    self.tx_repo.append(tx)
                    next_num += 1
                    imported += 1
                except (AppError, KeyError, ValueError):
                    skipped += 1
        return imported, skipped
