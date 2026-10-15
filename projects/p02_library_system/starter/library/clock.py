"""Injectable clocks so due dates and fines can be tested without waiting."""

# The imports below are the ones your implementation will need.
# ruff: noqa: F401

from datetime import date, timedelta
from typing import Protocol


class Clock(Protocol):
    """Anything that can report today's date."""

    def today(self) -> date:
        """Return the current date."""
        ...


class SystemClock:
    """A clock that reads the real calendar."""

    def today(self) -> date:
        """Return the real current date.

        Returns:
            ``date.today()``.
        """
        # TODO: Return date.today().
        raise NotImplementedError


class FixedClock:
    """A clock frozen at a chosen date that tests can move forward.

    Args:
        start: The date the clock reports until it is advanced.
    """

    def __init__(self, start: date) -> None:
        """Create a clock that reports ``start``."""
        self._today = start

    def today(self) -> date:
        """Return the clock's current date.

        Returns:
            The date set at construction, plus any advances.
        """
        # TODO: Return the stored date.
        raise NotImplementedError

    def advance(self, days: int) -> None:
        """Move the clock forward.

        Args:
            days: Number of days to add; must not be negative.

        Raises:
            ValueError: If ``days`` is negative.
        """
        # TODO: Reject negative days with ValueError; add timedelta(days=days) to the stored date.
        raise NotImplementedError
