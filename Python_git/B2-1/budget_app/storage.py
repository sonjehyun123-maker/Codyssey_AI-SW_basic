import json
import os
from typing import Dict, Iterator, List, Optional

from .models import Transaction


class TransactionRepository:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").close()

    def append(self, tx: Transaction) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")

    def stream_all(self) -> Iterator[Transaction]:
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield Transaction.from_dict(json.loads(line))

    def next_id(self) -> str:
        max_num = 0
        for tx in self.stream_all():
            max_num = max(max_num, int(tx.id.split("-")[1]))
        return f"TX-{max_num + 1:06d}"

    def rewrite_all(self, transactions: List[Transaction]) -> None:
        tmp_path = self.path + ".tmp"
        bak_path = self.path + ".bak"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                for tx in transactions:
                    f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")
            # 백업 생성 후 원자적 교체
            if os.path.exists(self.path):
                import shutil
                shutil.copy2(self.path, bak_path)
            os.replace(tmp_path, self.path)
            if os.path.exists(bak_path):
                os.remove(bak_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(bak_path) and not os.path.exists(self.path):
                os.replace(bak_path, self.path)
            raise


class CategoryStore:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").close()

    def list_all(self) -> List[str]:
        with open(self.path, "r", encoding="utf-8") as f:
            return [json.loads(line)["name"] for line in f if line.strip()]

    def add(self, name: str) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")

    def remove(self, name: str) -> None:
        remaining = [c for c in self.list_all() if c != name]
        tmp_path = self.path + ".tmp"
        bak_path = self.path + ".bak"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                for c in remaining:
                    f.write(json.dumps({"name": c}, ensure_ascii=False) + "\n")
            if os.path.exists(self.path):
                import shutil
                shutil.copy2(self.path, bak_path)
            os.replace(tmp_path, self.path)
            if os.path.exists(bak_path):
                os.remove(bak_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(bak_path) and not os.path.exists(self.path):
                os.replace(bak_path, self.path)
            raise


class BudgetStore:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            open(path, "w", encoding="utf-8").close()

    def get_all(self) -> Dict[str, int]:
        budgets: Dict[str, int] = {}
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    budgets[d["month"]] = d["amount"]
        return budgets

    def set(self, month: str, amount: int) -> None:
        budgets = self.get_all()
        budgets[month] = amount
        tmp_path = self.path + ".tmp"
        bak_path = self.path + ".bak"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                for m, a in budgets.items():
                    f.write(json.dumps({"month": m, "amount": a}, ensure_ascii=False) + "\n")
            if os.path.exists(self.path):
                import shutil
                shutil.copy2(self.path, bak_path)
            os.replace(tmp_path, self.path)
            if os.path.exists(bak_path):
                os.remove(bak_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if os.path.exists(bak_path) and not os.path.exists(self.path):
                os.replace(bak_path, self.path)
            raise

    def get(self, month: str) -> Optional[int]:
        return self.get_all().get(month)

