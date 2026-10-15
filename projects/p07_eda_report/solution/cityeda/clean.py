"""Cleaning rules for raw 311 data, each one recorded in a cleaning log."""

from dataclasses import dataclass

import pandas as pd

from cityeda.generate import TIMESTAMP_FORMAT

UNKNOWN_BOROUGH = "Unknown"

BOROUGH_ALIASES: dict[str, str] = {
    "manhattan": "Manhattan",
    "new york": "Manhattan",
    "mn": "Manhattan",
    "brooklyn": "Brooklyn",
    "bklyn": "Brooklyn",
    "bk": "Brooklyn",
    "queens": "Queens",
    "qn": "Queens",
    "bronx": "Bronx",
    "bx": "Bronx",
    "staten island": "Staten Island",
    "si": "Staten Island",
}


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
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return UNKNOWN_BOROUGH
    key = " ".join(str(value).split()).casefold()
    key = key.removeprefix("the ")
    return BOROUGH_ALIASES.get(key, UNKNOWN_BOROUGH)


def normalize_category(value: object) -> str | None:
    """Trim and title-case a complaint category (``" NOISE "`` becomes ``"Noise"``).

    Args:
        value: Raw category text; may be missing.

    Returns:
        The normalized category, or ``None`` when missing.
    """
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    return " ".join(str(value).split()).title()


def clean_requests(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[CleaningStep]]:
    """Apply every cleaning rule in order and log what each one did.

    Rules, in order:

    1. ``drop_duplicate_ids``: keep the first row for each ``request_id``.
    2. ``normalize_category``: trim and title-case categories.
    3. ``normalize_borough``: map spelling variants to five canonical boroughs.
    4. ``fill_missing_borough``: blank boroughs become ``"Unknown"``.
    5. ``drop_invalid_created``: drop rows whose ``created_at`` does not parse.
    6. ``null_invalid_closed``: an unparseable ``closed_at`` becomes missing (resolution unknown).
    7. ``null_closed_before_created``: a ``closed_at`` earlier than ``created_at`` becomes missing.

    The input is not modified. The result is sorted by ``created_at`` then ``request_id`` with a fresh index.

    Args:
        raw: Frame from ``load_requests``.

    Returns:
        The cleaned frame (``created_at``/``closed_at`` as ``datetime64``) and the cleaning log.
    """
    log: list[CleaningStep] = []
    df = raw.drop_duplicates(subset="request_id", keep="first")
    log.append(
        CleaningStep("drop_duplicate_ids", "Removed repeated request IDs, keeping the first.", len(raw) - len(df))
    )

    category = df["category"].map(normalize_category)
    changed = int((category != df["category"]).sum())
    df = df.assign(category=category)
    log.append(CleaningStep("normalize_category", "Trimmed whitespace and title-cased categories.", changed))

    missing_borough = df["borough"].isna() | (df["borough"].str.strip() == "")
    borough = df["borough"].map(normalize_borough)
    renamed = int(((borough != df["borough"]) & ~missing_borough).sum())
    df = df.assign(borough=borough)
    log.append(CleaningStep("normalize_borough", "Mapped borough spellings to canonical names.", renamed))
    log.append(CleaningStep("fill_missing_borough", "Blank boroughs labelled 'Unknown'.", int(missing_borough.sum())))

    created = pd.to_datetime(df["created_at"], format=TIMESTAMP_FORMAT, errors="coerce")
    valid = created.notna()
    df = df.assign(created_at=created)[valid]
    log.append(
        CleaningStep(
            "drop_invalid_created", "Dropped rows whose created_at is not a valid timestamp.", int((~valid).sum())
        )
    )

    closed = pd.to_datetime(df["closed_at"], format=TIMESTAMP_FORMAT, errors="coerce")
    bad_closed = closed.isna() & df["closed_at"].notna()
    df = df.assign(closed_at=closed)
    log.append(CleaningStep("null_invalid_closed", "Unparseable closed_at set to missing.", int(bad_closed.sum())))

    backwards = df["closed_at"] < df["created_at"]
    df = df.assign(closed_at=df["closed_at"].mask(backwards))
    log.append(
        CleaningStep(
            "null_closed_before_created", "closed_at earlier than created_at set to missing.", int(backwards.sum())
        )
    )

    df = df.sort_values(["created_at", "request_id"], kind="stable").reset_index(drop=True)
    return df, log
