"""Validate: a small rule engine that splits raw rows into valid rows and rejections with reasons."""

import json
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, tzinfo
from pathlib import Path

from etl.models import LOCAL_TZ, TRIP_FIELDS, RawRow, Rejection

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
    moment = datetime.fromisoformat(value.strip())
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=local_tz)
    return moment.astimezone(UTC)


def _required(row: RawRow) -> list[str]:
    if "_error" in row:
        return [row["_error"]]
    return [f"missing:{name}" for name in TRIP_FIELDS if not row.get(name, "").strip()]


def _timestamps(row: RawRow) -> list[str]:
    reasons: list[str] = []
    parsed: dict[str, datetime] = {}
    for name in ("start_time", "end_time"):
        value = row.get(name, "")
        if not value.strip():
            continue
        try:
            parsed[name] = parse_timestamp(value)
        except ValueError:
            reasons.append(f"bad_timestamp:{name}")
    if len(parsed) == 2:
        span = parsed["end_time"] - parsed["start_time"]
        if span <= timedelta(0):
            reasons.append("end_before_start")
        elif span > MAX_DURATION:
            reasons.append("duration_too_long")
    return reasons


def _member_type(row: RawRow) -> list[str]:
    value = row.get("member_type", "")
    return [] if not value or value in MEMBER_TYPES else ["bad_member_type"]


def station_rule(known_station_ids: Iterable[str]) -> Rule:
    """Build a rule that rejects trips referencing stations not in the reference data.

    Args:
        known_station_ids: Every valid station id.

    Returns:
        The rule.
    """
    known = frozenset(known_station_ids)

    def check(row: RawRow) -> list[str]:
        return [
            f"unknown_station:{name}"
            for name in ("start_station_id", "end_station_id")
            if row.get(name) and row[name] not in known
        ]

    return Rule("known_stations", check)


def default_rules(known_station_ids: Iterable[str]) -> list[Rule]:
    """Return the standard trip rules.

    Args:
        known_station_ids: Every valid station id.

    Returns:
        Rules for required fields, timestamps, member type, and station references.
    """
    return [
        Rule("required_fields", _required),
        Rule("timestamps", _timestamps),
        Rule("member_type", _member_type),
        station_rule(known_station_ids),
    ]


def validate(rows: Iterable[RawRow], rules: list[Rule]) -> ValidationResult:
    """Run every rule on every row and collect all reasons per row.

    Running all rules (instead of stopping at the first failure) gives the data provider one complete report.

    Args:
        rows: Raw rows.
        rules: Rules to apply.

    Returns:
        Valid rows and rejections.
    """
    result = ValidationResult()
    for row in rows:
        reasons = [reason for rule in rules for reason in rule.check(row)]
        if reasons:
            result.rejected.append(Rejection(row=row, reasons=tuple(reasons)))
        else:
            result.valid.append(row)
    return result


def reason_counts(rejected: Iterable[Rejection]) -> dict[str, int]:
    """Count rejections per reason code.

    Args:
        rejected: Rejections.

    Returns:
        Reason code to count, sorted by code.
    """
    counts = Counter(reason for r in rejected for reason in r.reasons)
    return dict(sorted(counts.items()))


def write_rejection_report(rejected: Iterable[Rejection], path: Path) -> int:
    """Append rejections to a JSON Lines report, one object per rejected row.

    Args:
        rejected: Rejections to write.
        path: Report file; created if missing.

    Returns:
        Number of lines written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("a", encoding="utf-8") as fh:
        for r in rejected:
            fh.write(json.dumps({"reasons": list(r.reasons), "row": r.row}, sort_keys=True) + "\n")
            written += 1
    return written
