from dataclasses import dataclass, field
from typing import List


@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": self.tags,
        }

    @staticmethod
    def from_dict(d: dict) -> "Transaction":
        return Transaction(
            id=d["id"],
            type=d["type"],
            date=d["date"],
            amount=int(d["amount"]),
            category=d["category"],
            memo=d.get("memo", ""),
            tags=d.get("tags", []),
        )
