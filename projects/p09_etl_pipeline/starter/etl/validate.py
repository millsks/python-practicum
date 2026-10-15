"""Validate: a small rule engine that splits raw rows into valid rows and rejections with reasons."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, tzinfo
from pathlib import Path

from etl.models import LOCAL_TZ, RawRow, Rejection

MAX_DURATION = timedelta(hours=24)
MEMBER_TYPES = frozenset({"member", "casual"})

Check = Callable[[RawRow], list[str]]
"""A rule's check: return a list of reason codes, empty when the row passes."""


@dataclass(frozen=True, slots=True)
class Rule:
    """A named validation rule.

    Attributes:
        name: Short rule name, used in documentation and logs.
        check: Function returning reason codes for a failing row (empty list when it passes).
    """

    name: str
    check: Check


@dataclass(slots=True)
class ValidationResult:
    """Output of :func:`validate`.

    Attributes:
        valid: Rows that passed every rule, in input order.
        rejected: Rows that failed at least one rule, with every reason.
    """

    valid: list[RawRow] = field(default_factory=list)
    rejected: list[Rejection] = field(default_factory=list)


def parse_timestamp(value: str, local_tz: tzinfo = LOCAL_TZ) -> datetime:
    """Parse a raw timestamp into an aware UTC datetime.

    Strings with an offset (``2026-03-05T08:15:00-05:00``) keep it; naive strings (``2026-03-05 08:15:00``) are
    interpreted in ``local_tz``. Both are converted to UTC.

    Args:
        value: Raw timestamp text.
        local_tz: Zone for naive timestamps.

    Returns:
        The instant in UTC.

    Raises:
        ValueError: If the text is not an ISO-8601 timestamp.
    """
    # TODO: datetime.fromisoformat; naive -> replace(tzinfo=local_tz); then astimezone(UTC)
    raise NotImplementedError


def _required(row: RawRow) -> list[str]:
    # TODO: an '_error' row -> [row['_error']]; else 'missing:<field>' for each blank TRIP_FIELDS entry
    raise NotImplementedError


def _timestamps(row: RawRow) -> list[str]:
    # TODO: 'bad_timestamp:<field>' on ValueError; 'end_before_start' if end <= start; 'duration_too_long' if > MAX_DURATION
    raise NotImplementedError


def _member_type(row: RawRow) -> list[str]:
    # TODO: 'bad_member_type' unless blank (handled by _required) or in MEMBER_TYPES
    raise NotImplementedError


def station_rule(known_station_ids: Iterable[str]) -> Rule:
    """Build a rule that rejects trips referencing stations not in the reference data.

    Args:
        known_station_ids: Every valid station id.

    Returns:
        The rule.
    """
    # TODO: return Rule('known_stations', check) where check yields 'unknown_station:<field>'
    raise NotImplementedError


def default_rules(known_station_ids: Iterable[str]) -> list[Rule]:
    """Return the standard trip rules.

    Args:
        known_station_ids: Every valid station id.

    Returns:
        Rules for required fields, timestamps, member type, and station references.
    """
    # TODO: required fields, timestamps, member type, station_rule(known_station_ids)
    raise NotImplementedError


def validate(rows: Iterable[RawRow], rules: list[Rule]) -> ValidationResult:
    """Run every rule on every row and collect all reasons per row.

    Running all rules (instead of stopping at the first failure) gives the data provider one complete report.

    Args:
        rows: Raw rows.
        rules: Rules to apply.

    Returns:
        Valid rows and rejections.
    """
    # TODO: run every rule on every row; collect ALL reasons; split into valid / rejected
    raise NotImplementedError


def reason_counts(rejected: Iterable[Rejection]) -> dict[str, int]:
    """Count rejections per reason code.

    Args:
        rejected: Rejections.

    Returns:
        Reason code to count, sorted by code.
    """
    # TODO: collections.Counter over every reason, returned as a dict sorted by key
    raise NotImplementedError


def write_rejection_report(rejected: Iterable[Rejection], path: Path) -> int:
    """Append rejections to a JSON Lines report, one object per rejected row.

    Args:
        rejected: Rejections to write.
        path: Report file; created if missing.

    Returns:
        Number of lines written.
    """
    # TODO: append json.dumps({'reasons': [...], 'row': {...}}, sort_keys=True) lines
    raise NotImplementedError
