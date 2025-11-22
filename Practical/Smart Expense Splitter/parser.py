"""Expense parsing utilities.

Handlers for parsing expense data from various input formats (text strings, files).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Iterable, List, Sequence, Optional, Union

try:
    from .models import Expense, Participant
except ImportError:
    from models import Expense, Participant


@dataclass
class ExpenseInputParser:
    """Parse expense strings with the format 'description;amount;payer;consumer1,consumer2'.

    Attributes:
        delimiter: Separator between main fields (default ';').
        consumer_delimiter: Separator between consumer names (default ',').
    """

    delimiter: str = ";"
    consumer_delimiter: str = ","

    def parse(self, raw: str) -> Expense:
        """Parse a single line into an Expense object.

        Args:
            raw: The input string.

        Returns:
            Expense: The parsed object.

        Raises:
            ValueError: If the input format is invalid.
        """
        parts = [part.strip() for part in raw.split(self.delimiter)]
        if len(parts) != 4:
            raise ValueError(
                "Expense input must contain description, amount, payer and consumers separated by ';'"
            )
        description, amount_raw, payer_name, consumers_raw = parts
        amount = Decimal(amount_raw)
        payer = Participant(payer_name)
        consumers = [
            Participant(name.strip())
            for name in consumers_raw.split(self.consumer_delimiter)
            if name.strip()
        ]
        if not consumers:
            raise ValueError("Expense must include at least one consumer")
        return Expense(
            description=description, amount=amount, payer=payer, consumers=consumers
        )

    def parse_many(self, rows: Iterable[str]) -> List[Expense]:
        """Parse multiple expense strings.

        Args:
            rows: Iterable of strings.

        Returns:
            List[Expense]: List of parsed Expense objects.
        """
        return [self.parse(row) for row in rows if row.strip()]


def load_expenses_from_file(
    path: Union[str, Path], parser: Optional[ExpenseInputParser] = None
) -> List[Expense]:
    """Load expenses from a text file.

    Args:
        path: Path to the file.
        parser: Custom parser instance.

    Returns:
        List[Expense]: Parsed expenses.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    parser = parser or ExpenseInputParser()
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    with file_path.open("r", encoding="utf-8") as handle:
        return parser.parse_many(handle.readlines())


def parse_cli_expenses(
    expense_args: Sequence[str], parser: Optional[ExpenseInputParser] = None
) -> List[Expense]:
    """Parse expenses provided as command-line arguments.

    Args:
        expense_args: Sequence of expense strings.
        parser: Custom parser instance.

    Returns:
        List[Expense]: Parsed expenses.
    """
    parser = parser or ExpenseInputParser()
    return parser.parse_many(expense_args)
