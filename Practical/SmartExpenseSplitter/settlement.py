"""Settlement algorithms for minimizing cash flow between participants.

Provides logic to simplify a web of debts into a concise list of transactions.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Any

from .models import DebtGraph, Participant, PaymentPlanEntry, Expense, quantize_money


@dataclass
class SettlementPlan:
    """Collection of payment plan entries.

    Attributes:
        entries: List of transactions needed to settle debts.
    """

    entries: List[PaymentPlanEntry]

    def total_transactions(self) -> int:
        """Get the count of transactions."""
        return len(self.entries)

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert plan to a list of dictionaries."""
        return [entry.to_dict() for entry in self.entries]


def build_balance_sheet(expenses: Iterable[Expense]) -> Dict[str, Decimal]:
    """Calculate net balances for all participants.

    Args:
        expenses: Iterable of expenses.

    Returns:
        Dict[str, Decimal]: Map of name to net balance.
    """
    graph = DebtGraph.from_expenses(expenses)
    return graph.balances


def optimize_settlements(expenses: Iterable[Expense]) -> SettlementPlan:
    """Compute a settlement plan that resolves all debts.

    Uses a greedy algorithm: match the biggest debtor with the biggest creditor.
    This minimizes the number of transactions in many cases (though not strictly optimal for all graphs).

    Args:
        expenses: Iterable of expenses.

    Returns:
        SettlementPlan: The list of payments to make.
    """
    graph = DebtGraph.from_expenses(expenses)

    # Ensure money is quantized before processing to avoid precision artifacts
    balances = {name: quantize_money(balance) for name, balance in graph.balances.items()}

    # Filter out zero balances
    creditors = {name: bal for name, bal in balances.items() if bal > 0}
    debtors = {name: bal for name, bal in balances.items() if bal < 0}

    entries: List[PaymentPlanEntry] = []

    # Greedy settlement loop
    while creditors and debtors:
        # Find max creditor and max debtor (most negative)
        creditor_name = max(creditors, key=creditors.get)  # type: ignore
        debtor_name = min(debtors, key=debtors.get)        # type: ignore

        creditor_amount = creditors[creditor_name]
        debtor_amount = debtors[debtor_name]

        # Amount to transfer is the minimum of what one owes and the other is owed
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

        # Update balances
        new_creditor_bal = quantize_money(creditor_amount - settlement_amount)
        new_debtor_bal = quantize_money(debtor_amount + settlement_amount)

        creditors[creditor_name] = new_creditor_bal
        debtors[debtor_name] = new_debtor_bal

        # Remove settled participants
        if creditors[creditor_name] == 0:
            del creditors[creditor_name]
        if debtors[debtor_name] == 0:
            del debtors[debtor_name]

    return SettlementPlan(entries)
