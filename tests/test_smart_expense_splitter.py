from decimal import Decimal

from Practical.SmartExpenseSplitter.models import Expense, Participant
from Practical.SmartExpenseSplitter.settlement import (
    build_balance_sheet,
    optimize_settlements,
)


def sample_expenses():
    alice = Participant("Alice")
    bob = Participant("Bob")
    carla = Participant("Carla")
    return [
        Expense("Groceries", Decimal("120.00"), alice, [alice, bob, carla]),
        Expense("Museum", Decimal("60.00"), bob, [alice, bob, carla]),
        Expense("Dinner", Decimal("90.00"), carla, [bob, carla]),
    ]


def test_build_balance_sheet():
    balances = build_balance_sheet(sample_expenses())
    assert balances["Alice"].quantize(Decimal("0.01")) == Decimal("60.00")
    assert balances["Bob"].quantize(Decimal("0.01")) == Decimal("-45.00")
    assert balances["Carla"].quantize(Decimal("0.01")) == Decimal("-15.00")


def test_optimize_settlements_minimizes_transactions():
    plan = optimize_settlements(sample_expenses())
    assert plan.total_transactions() == 2
    payouts = {
        (entry.payer.name, entry.receiver.name): entry.amount for entry in plan.entries
    }
    assert payouts[("Bob", "Alice")] == Decimal("45.00")
    assert payouts[("Carla", "Alice")] == Decimal("15.00")
