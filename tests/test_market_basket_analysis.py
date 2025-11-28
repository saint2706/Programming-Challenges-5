from __future__ import annotations

import math
from typing import List, Set

import pytest

from ArtificialIntelligence.market_basket_analysis import (
    apriori,
    generate_association_rules,
)


@pytest.fixture()
def small_transactions() -> List[Set[str]]:
    return [
        {"milk", "bread"},
        {"milk", "bread", "butter"},
        {"bread", "butter"},
        {"milk", "bread"},
    ]


def test_apriori_generates_expected_frequent_itemsets(
    small_transactions: List[Set[str]],
) -> None:
    frequent_itemsets = apriori(small_transactions, min_support=0.5)

    expected_supports = {
        frozenset({"milk"}): 0.75,
        frozenset({"bread"}): 1.0,
        frozenset({"butter"}): 0.5,
        frozenset({"milk", "bread"}): 0.75,
        frozenset({"bread", "butter"}): 0.5,
    }

    assert frequent_itemsets == expected_supports


def test_association_rules_compute_confidence_and_lift(
    small_transactions: List[Set[str]],
) -> None:
    frequent_itemsets = apriori(small_transactions, min_support=0.5)
    rules = generate_association_rules(frequent_itemsets, min_confidence=0.6)

    rules_lookup = {(rule.antecedent, rule.consequent): rule for rule in rules}

    milk_to_bread = rules_lookup[(frozenset({"milk"}), frozenset({"bread"}))]
    assert math.isclose(milk_to_bread.support, 0.75)
    assert math.isclose(milk_to_bread.confidence, 1.0)
    assert math.isclose(milk_to_bread.lift, 1.0)

    butter_to_bread = rules_lookup[(frozenset({"butter"}), frozenset({"bread"}))]
    assert math.isclose(butter_to_bread.confidence, 1.0)
    assert math.isclose(butter_to_bread.lift, 1.0)

    bread_to_milk = rules_lookup[(frozenset({"bread"}), frozenset({"milk"}))]
    assert math.isclose(bread_to_milk.confidence, 0.75)
    assert math.isclose(bread_to_milk.lift, 1.0)
