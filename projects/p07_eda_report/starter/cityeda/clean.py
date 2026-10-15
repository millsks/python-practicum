"""Cleaning rules for raw 311 data, each one recorded in a cleaning log."""

from dataclasses import dataclass

import pandas as pd

UNKNOWN_BOROUGH = "Unknown"

# TODO: map every lower-case spelling you find in the raw data to its canonical borough. Explore first:
#   raw["borough"].str.strip().str.casefold().value_counts()
BOROUGH_ALIASES: dict[str, str] = {}


@dataclass(frozen=True, slots=True)
class CleaningStep:
    """One applied cleaning rule.

    Attributes:
        rule: Short machine-friendly rule name, such as ``"drop_duplicate_ids"``.
        description: One sentence a reader of the report can understand.
        rows_affected: How many rows the rule changed or removed.
    """

    rule: str
    description: str
    rows_affected: int


def normalize_borough(value: object) -> str:
    """Map one raw borough spelling to its canonical name.

    Whitespace is collapsed, case is ignored, and a leading ``"the "`` is dropped before the alias lookup.

    Args:
        value: A raw borough value; may be missing (``None``/``NaN``) or blank.

    Returns:
        The canonical borough, or ``"Unknown"`` for missing or unrecognized values.
    """
    # TODO: handle None/NaN first (pd.isna), then " ".join(text.split()).casefold().removeprefix("the ").
    raise NotImplementedError


def normalize_category(value: object) -> str | None:
    """Trim and title-case a complaint category (``" NOISE "`` becomes ``"Noise"``).

    Args:
        value: Raw category text; may be missing.

    Returns:
        The normalized category, or ``None`` when missing.
    """
    raise NotImplementedError


def clean_requests(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[CleaningStep]]:
    """Apply every cleaning rule in order and log what each one did.

    Rules, in order:

    1. ``drop_duplicate_ids``: keep the first row for each ``request_id``.
    2. ``normalize_category``: trim and title-case categories.
    3. ``normalize_borough``: map spelling variants to five canonical boroughs (count non-blank rows changed).
    4. ``fill_missing_borough``: blank boroughs become ``"Unknown"`` (count the blanks).
    5. ``drop_invalid_created``: drop rows whose ``created_at`` does not parse.
    6. ``null_invalid_closed``: an unparseable ``closed_at`` becomes missing (resolution unknown).
    7. ``null_closed_before_created``: a ``closed_at`` earlier than ``created_at`` becomes missing.

    The input is not modified. The result is sorted by ``created_at`` then ``request_id`` with a fresh index.

    Args:
        raw: Frame from ``load_requests``.

    Returns:
        The cleaned frame (``created_at``/``closed_at`` as ``datetime64``) and the cleaning log.
    """
    # TODO: build the log as you go: log.append(CleaningStep("drop_duplicate_ids", "...", removed_count)).
    # TODO: import TIMESTAMP_FORMAT from cityeda.generate and parse dates with
    #   pd.to_datetime(..., format=TIMESTAMP_FORMAT, errors="coerce"); NaT marks a bad value.
    # TODO: use df.assign(...) and Series.mask(...) instead of chained assignment (Copy-on-Write!).
    raise NotImplementedError
