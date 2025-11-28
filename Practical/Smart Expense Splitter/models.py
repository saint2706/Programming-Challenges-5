"""Domain models for the Smart Expense Splitter.

Defines the core entities like Participant, Expense, and the DebtGraph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Dict, Any

MONEY_CONTEXT = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round a decimal to two places using bankers rounding.

    Args:
        value: The decimal value to round.

    Returns:
        Decimal: Rounded value.
    """
    return value.quantize(MONEY_CONTEXT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Participant:
    """Person participating in expenses.

    Attributes:
        name: Unique identifier/name for the participant.
    """

    name: str

    def __post_init__(self) -> None:
        """
        Docstring for __post_init__.
        """
        if not self.name:
            raise ValueError("Participant name cannot be empty")


@dataclass(frozen=True)
class Expense:
    """Expense paid by a participant for a group of participants.

    Attributes:
        description: What the expense was for.
        amount: Total cost.
        payer: Who paid.
        consumers: Who benefited/should share the cost.
    """

    description: str
    amount: Decimal
    payer: Participant
    consumers: List[Participant] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Docstring for __post_init__.
        """
        if self.amount <= 0:
            raise ValueError("Expense amount must be positive")
        if not self.consumers:
            raise ValueError("Expense must have at least one consumer")

    @property
    def split_amount(self) -> Decimal:
        """Calculate the amount each consumer owes (evenly split).

        Returns:
            Decimal: Share per person.
        """
        share = self.amount / Decimal(len(self.consumers))
        return quantize_money(share)


@dataclass(frozen=True)
class PaymentPlanEntry:
    """Represents a single transaction to settle debts.

    Attributes:
        payer: Who sends money.
        receiver: Who receives money.
        amount: How much to transfer.
    """

    payer: Participant
    receiver: Participant
    amount: Decimal

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization.

        Returns:
            dict: JSON-serializable representation.
        """
        return {
            "from": self.payer.name,
            "to": self.receiver.name,
            "amount": f"{self.amount:.2f}",
        }


@dataclass
class DebtGraph:
    """Directed graph storing balances between participants.

    Attributes:
        balances: Mapping of participant name to their net balance.
                  Positive balance = is owed money (creditor).
                  Negative balance = owes money (debtor).
    """

    balances: Dict[str, Decimal]

    @classmethod
    def from_expenses(cls, expenses: Iterable[Expense]) -> "DebtGraph":
        """Build the debt graph from a list of expenses.

        Args:
            expenses: List of Expense objects.

        Returns:
            DebtGraph: The calculated debt graph.
        """
        balances: Dict[str, Decimal] = {}
        for expense in expenses:
            share = expense.split_amount
            payer_key = expense.payer.name

            # Payer gets credit for the full amount paid
            balances[payer_key] = balances.get(payer_key, Decimal("0")) + expense.amount

            # Consumers incur debt for their share
            for consumer in expense.consumers:
                key = consumer.name
                balances[key] = balances.get(key, Decimal("0")) - share
        return cls(balances)

    def creditors(self) -> Dict[str, Decimal]:
        """Get participants who are owed money.

        Returns:
            Dict[str, Decimal]: Map of name to positive balance.
        """
        return {name: bal for name, bal in self.balances.items() if bal > Decimal("0")}

    def debtors(self) -> Dict[str, Decimal]:
        """Get participants who owe money.

        Returns:
            Dict[str, Decimal]: Map of name to negative balance.
        """
        return {name: bal for name, bal in self.balances.items() if bal < Decimal("0")}
