"""Domain models for the Smart Expense Splitter."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List

MONEY_CONTEXT = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round a decimal to two places using bankers rounding."""

    return value.quantize(MONEY_CONTEXT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Participant:
    """Person participating in expenses."""

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Participant name cannot be empty")


@dataclass(frozen=True)
class Expense:
    """Expense paid by a participant for a group of participants."""

    description: str
    amount: Decimal
    payer: Participant
    consumers: List[Participant] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("Expense amount must be positive")
        if not self.consumers:
            raise ValueError("Expense must have at least one consumer")

    @property
    def split_amount(self) -> Decimal:
        share = self.amount / Decimal(len(self.consumers))
        return quantize_money(share)


@dataclass(frozen=True)
class PaymentPlanEntry:
    """Represents a single transaction to settle debts."""

    payer: Participant
    receiver: Participant
    amount: Decimal

    def to_dict(self) -> dict:
        return {
            "from": self.payer.name,
            "to": self.receiver.name,
            "amount": f"{self.amount:.2f}",
        }


@dataclass
class DebtGraph:
    """Directed graph storing balances between participants."""

    balances: dict[str, Decimal]

    @classmethod
    def from_expenses(cls, expenses: Iterable[Expense]) -> "DebtGraph":
        balances: dict[str, Decimal] = {}
        for expense in expenses:
            share = expense.split_amount
            payer_key = expense.payer.name
            balances[payer_key] = balances.get(payer_key, Decimal("0")) + expense.amount
            for consumer in expense.consumers:
                key = consumer.name
                balances[key] = balances.get(key, Decimal("0")) - share
        return cls(balances)

    def creditors(self) -> dict[str, Decimal]:
        return {name: bal for name, bal in self.balances.items() if bal > Decimal("0")}

    def debtors(self) -> dict[str, Decimal]:
        return {name: bal for name, bal in self.balances.items() if bal < Decimal("0")}
