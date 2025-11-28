"""
Artificial Intelligence project implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, List, Mapping, MutableMapping, Sequence, Set


@dataclass(frozen=True)
class AssociationRule:
    """Represents an association rule with its key metrics.

    Attributes:
        antecedent: Items that imply the consequent.
        consequent: Items implied by the antecedent.
        support: Support of the combined itemset ``antecedent ∪ consequent``.
        confidence: Probability of seeing the consequent given the antecedent.
        lift: How many times more often the antecedent and consequent occur together
            than if they were independent. Values greater than 1 indicate
            positive correlation.
    """

    antecedent: frozenset[str]
    consequent: frozenset[str]
    support: float
    confidence: float
    lift: float


def _validate_support(min_support: float) -> None:
    """Validate that support is a ratio between 0 and 1.

    Args:
        min_support: Minimum support ratio expected to be in the range ``(0, 1]``.

    Raises:
        ValueError: If the supplied support value is outside the valid range.
    """

    if not 0 < min_support <= 1:
        raise ValueError("min_support must be in the range (0, 1]")


def _candidate_itemsets(previous_level: Set[frozenset[str]], k: int) -> Set[frozenset[str]]:
    """Generate candidate itemsets of size ``k`` from the previous level.

    Args:
        previous_level: Frequent itemsets of size ``k-1``.
        k: Desired size of the candidate itemsets.

    Returns:
        A set of candidate itemsets of size ``k``.
    """

    candidates: Set[frozenset[str]] = set()
    prev_list = list(previous_level)
    for i, itemset_a in enumerate(prev_list):
        for itemset_b in prev_list[i + 1 :]:
            union = itemset_a | itemset_b
            if len(union) == k:
                candidates.add(union)
    return candidates


def apriori(transactions: Sequence[Iterable[str]], min_support: float) -> MutableMapping[frozenset[str], float]:
    """Run the Apriori algorithm to find frequent itemsets.

    Args:
        transactions: A sequence of baskets where each basket contains hashable
            items (e.g., ``{"milk", "bread"}``).
        min_support: Minimum support ratio required for an itemset to be
            considered frequent.

    Returns:
        A mapping from frequent itemsets to their support values.

    Raises:
        ValueError: If ``min_support`` is outside ``(0, 1]`` or no transactions
            are provided.
    """

    _validate_support(min_support)
    transaction_list: List[Set[str]] = [set(t) for t in transactions]
    if not transaction_list:
        raise ValueError("At least one transaction is required")

    total_transactions = len(transaction_list)
    min_support_count = min_support * total_transactions

    # Initialize with single-item supports.
    item_counts: MutableMapping[frozenset[str], int] = {}
    for basket in transaction_list:
        for item in basket:
            key = frozenset([item])
            item_counts[key] = item_counts.get(key, 0) + 1

    frequent_itemsets: MutableMapping[frozenset[str], float] = {
        itemset: count / total_transactions
        for itemset, count in item_counts.items()
        if count >= min_support_count
    }

    current_level = {itemset for itemset, support in frequent_itemsets.items() if len(itemset) == 1}
    k = 2

    while current_level:
        candidates = _candidate_itemsets(current_level, k)
        candidate_counts: MutableMapping[frozenset[str], int] = {c: 0 for c in candidates}

        for basket in transaction_list:
            for candidate in candidates:
                if candidate.issubset(basket):
                    candidate_counts[candidate] += 1

        next_level: Set[frozenset[str]] = set()
        for candidate, count in candidate_counts.items():
            if count >= min_support_count:
                support = count / total_transactions
                frequent_itemsets[candidate] = support
                next_level.add(candidate)

        current_level = next_level
        k += 1

    return frequent_itemsets


def generate_association_rules(
    frequent_itemsets: Mapping[frozenset[str], float],
    min_confidence: float = 0.0,
    min_lift: float = 0.0,
) -> List[AssociationRule]:
    """Derive association rules from frequent itemsets.

    Args:
        frequent_itemsets: Mapping of frequent itemsets to their support ratios.
            Supports must be calculated against the same transaction set.
        min_confidence: Minimum confidence threshold for a rule to be included.
        min_lift: Minimum lift threshold for a rule to be included.

    Returns:
        A list of :class:`AssociationRule` objects that satisfy the thresholds.
    """

    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be in the range [0, 1]")
    if min_lift < 0:
        raise ValueError("min_lift must be non-negative")

    rules: List[AssociationRule] = []
    for itemset, itemset_support in frequent_itemsets.items():
        if len(itemset) < 2:
            continue

        for i in range(1, len(itemset)):
            for antecedent in map(frozenset, combinations(itemset, i)):
                consequent = itemset - antecedent
                antecedent_support = frequent_itemsets.get(antecedent)
                consequent_support = frequent_itemsets.get(consequent)

                if antecedent_support is None or consequent_support is None:
                    continue

                confidence = itemset_support / antecedent_support
                lift = confidence / consequent_support

                if confidence >= min_confidence and lift >= min_lift:
                    rules.append(
                        AssociationRule(
                            antecedent=antecedent,
                            consequent=consequent,
                            support=itemset_support,
                            confidence=confidence,
                            lift=lift,
                        )
                    )

    return rules


def sample_transactions() -> List[Set[str]]:
    """Provide a small sample of grocery-style transactions for demos/tests."""

    return [
        {"milk", "bread", "eggs"},
        {"milk", "bread"},
        {"milk", "diapers", "beer", "bread"},
        {"bread", "diapers", "beer", "cola"},
        {"milk", "diapers", "bread", "beer"},
        {"diapers", "milk", "bread", "cola"},
    ]


def _format_itemset(itemset: frozenset[str]) -> str:
    """Format an itemset for pretty printing."""

    return "{" + ", ".join(sorted(itemset)) + "}"


def demo(min_support: float = 0.3, min_confidence: float = 0.6, min_lift: float = 1.0) -> None:
    """Run a simple demo using sample transactions.

    Args:
        min_support: Support threshold for frequent itemsets.
        min_confidence: Confidence threshold for rules.
        min_lift: Lift threshold for rules.
    """

    transactions = sample_transactions()
    frequent_itemsets = apriori(transactions, min_support=min_support)
    rules = generate_association_rules(
        frequent_itemsets, min_confidence=min_confidence, min_lift=min_lift
    )

    print("Frequent Itemsets:")
    for itemset, support in sorted(frequent_itemsets.items(), key=lambda x: (len(x[0]), x[0])):
        print(f"  {_format_itemset(itemset)} -> support: {support:.2f}")

    print("\nAssociation Rules:")
    for rule in sorted(rules, key=lambda r: (r.antecedent, r.consequent)):
        print(
            f"  {_format_itemset(rule.antecedent)} -> {_format_itemset(rule.consequent)} | "
            f"support: {rule.support:.2f}, confidence: {rule.confidence:.2f}, lift: {rule.lift:.2f}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Apriori market basket analysis demo.")
    parser.add_argument("--min-support", type=float, default=0.3, help="Minimum support ratio (0, 1].")
    parser.add_argument("--min-confidence", type=float, default=0.6, help="Minimum confidence for rules.")
    parser.add_argument("--min-lift", type=float, default=1.0, help="Minimum lift for rules.")
    args = parser.parse_args()

    demo(min_support=args.min_support, min_confidence=args.min_confidence, min_lift=args.min_lift)
