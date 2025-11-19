"""Settlement algorithms for minimizing cash flow between participants."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List

from .models import DebtGraph, Participant, PaymentPlanEntry, Expense, quantize_money


@dataclass
class SettlementPlan:
    """Collection of payment plan entries."""

    entries: List[PaymentPlanEntry]

    def total_transactions(self) -> int:
        return len(self.entries)

    def to_dict(self) -> List[dict]:
        return [entry.to_dict() for entry in self.entries]


def build_balance_sheet(expenses: Iterable[Expense]) -> Dict[str, Decimal]:
    graph = DebtGraph.from_expenses(expenses)
    return graph.balances


def optimize_settlements(expenses: Iterable[Expense]) -> SettlementPlan:
    graph = DebtGraph.from_expenses(expenses)
    balances = {name: quantize_money(balance) for name, balance in graph.balances.items()}

    creditors = {name: bal for name, bal in balances.items() if bal > 0}
    debtors = {name: bal for name, bal in balances.items() if bal < 0}

    entries: List[PaymentPlanEntry] = []
    while creditors and debtors:
        creditor_name = max(creditors, key=creditors.get)
        debtor_name = min(debtors, key=debtors.get)

        creditor_amount = creditors[creditor_name]
        debtor_amount = debtors[debtor_name]

        settlement_amount = quantize_money(min(creditor_amount, -debtor_amount))
        if settlement_amount == 0:
            break

        entries.append(
            PaymentPlanEntry(
                payer=Participant(debtor_name),
                receiver=Participant(creditor_name),
                amount=settlement_amount,
            )
        )

        creditors[creditor_name] = quantize_money(creditor_amount - settlement_amount)
        debtors[debtor_name] = quantize_money(debtor_amount + settlement_amount)

        if creditors[creditor_name] == 0:
            del creditors[creditor_name]
        if debtors[debtor_name] == 0:
            del debtors[debtor_name]

    return SettlementPlan(entries)
