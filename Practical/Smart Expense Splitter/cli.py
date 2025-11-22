"""Command line interface for the Smart Expense Splitter.

Allows users to input expenses via file or arguments and outputs a settlement plan.
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List

# Hack to support running as a script despite spaces in folder name
sys.path.append(os.path.dirname(__file__))
try:
    from parser import ExpenseInputParser, load_expenses_from_file, parse_cli_expenses
    from settlement import optimize_settlements
    from models import Expense
except ImportError:
    from .parser import ExpenseInputParser, load_expenses_from_file, parse_cli_expenses
    from .settlement import optimize_settlements
    from .models import Expense


def build_argument_parser() -> argparse.ArgumentParser:
    """Construct the argument parser.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    parser = argparse.ArgumentParser(
        description="Split shared expenses and minimize settlements"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Optional text file containing expenses formatted as description;amount;payer;consumer1,consumer2",
    )
    parser.add_argument(
        "--expense",
        action="append",
        default=[],
        help="Expense specified directly via CLI; can be repeated",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional path to save the settlement plan as JSON",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print settlement plan to stdout",
    )
    return parser


def load_expenses_from_sources(args: argparse.Namespace) -> List[Expense]:
    """Load expenses from file and CLI arguments.

    Args:
        args: Parsed arguments.

    Returns:
        List[Expense]: Combined list of expenses.
    """
    parser = ExpenseInputParser()
    expenses: List[Expense] = []
    if args.file:
        expenses.extend(load_expenses_from_file(args.file, parser=parser))
    if args.expense:
        expenses.extend(parse_cli_expenses(args.expense, parser=parser))
    if not expenses:
        raise SystemExit("No expenses provided. Use --file or --expense arguments.")
    return expenses


def main() -> None:
    """Entry point for the CLI."""
    parser = build_argument_parser()
    args = parser.parse_args()
    expenses = load_expenses_from_sources(args)
    settlement = optimize_settlements(expenses)

    plan_dict = settlement.to_dict()
    if args.output:
        Path(args.output).write_text(
            json.dumps(plan_dict, indent=2), encoding="utf-8"
        )

    if args.pretty or not args.output:
        if not plan_dict:
            print("All balances settled. No payments required.")
        else:
            print("Optimized Settlement Plan:")
            for entry in plan_dict:
                print(f" - {entry['from']} pays {entry['to']} {entry['amount']}")


if __name__ == "__main__":
    main()
