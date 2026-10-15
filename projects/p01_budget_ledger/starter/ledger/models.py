"""Plain data records shared by every ledger module."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

UNCATEGORIZED = "uncategorized"


@dataclass(frozen=True, slots=True)
class Transaction:
    """One row of a bank export.

    Attributes:
        date: Day the transaction posted.
        description: Merchant or memo text, as exported.
        amount: Signed amount; negative values are money spent, positive values are money received.
        category: Category assigned by the rules, or ``"uncategorized"``.
        source: Name of the file the row came from (ignored when comparing transactions).
        line: Line number in that file (ignored when comparing transactions).
    """

    date: date
    description: str
    amount: Decimal
    category: str = UNCATEGORIZED
    source: str = field(default="", compare=False)
    line: int = field(default=0, compare=False)

    @property
    def month(self) -> str:
        """The ``YYYY-MM`` month this transaction belongs to."""
        return f"{self.date:%Y-%m}"


@dataclass(frozen=True, slots=True)
class Rule:
    """Assign ``category`` to any description containing one of ``keywords``.

    Attributes:
        category: Category name to assign.
        keywords: Lower-case substrings to look for.
    """

    category: str
    keywords: tuple[str, ...]

    def matches(self, description: str) -> bool:
        """Return whether ``description`` contains any keyword, ignoring case.

        Args:
            description: Transaction description.

        Returns:
            True when at least one keyword occurs in the description.
        """
        text = description.casefold()
        return any(keyword in text for keyword in self.keywords)


@dataclass(frozen=True, slots=True)
class Config:
    """Categorization rules and monthly budget limits loaded from one file.

    Attributes:
        rules: Rules in priority order; the first match wins.
        budgets: Monthly spending limit per category.
    """

    rules: list[Rule] = field(default_factory=list)
    budgets: dict[str, Decimal] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Overrun:
    """A category whose spending exceeded its limit in one month.

    Attributes:
        month: ``YYYY-MM`` month.
        category: Category name.
        limit: Budgeted limit.
        spent: Amount actually spent (a positive number).
    """

    month: str
    category: str
    limit: Decimal
    spent: Decimal

    @property
    def over(self) -> Decimal:
        """How much more than the limit was spent."""
        return self.spent - self.limit
