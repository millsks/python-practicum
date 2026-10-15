"""Deterministic synthetic 311 service-request data with realistic mess.

This module is provided complete in the starter: it is the dataset, not part of the exercise. Every kind of mess is
injected into a known, disjoint set of rows so the cleaning rules have exact, testable effects.
"""

import csv
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np

COLUMNS: tuple[str, ...] = ("request_id", "created_at", "closed_at", "category", "borough", "channel", "status")
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
START = np.datetime64("2025-01-06T00:00:00")  # a Monday
WEEKS = 26

CATEGORIES: dict[str, tuple[float, float]] = {
    # name: (probability, median resolution hours)
    "Noise": (0.24, 6.0),
    "Heat/Hot Water": (0.18, 30.0),
    "Illegal Parking": (0.16, 4.0),
    "Street Condition": (0.13, 120.0),
    "Sanitation": (0.12, 48.0),
    "Water Leak": (0.09, 72.0),
    "Street Light": (0.08, 160.0),
}

BOROUGHS: dict[str, tuple[float, float, tuple[str, ...]]] = {
    # canonical name: (probability, resolution-time multiplier, messy spellings seen in the raw feed)
    "Brooklyn": (0.30, 1.0, ("BROOKLYN", "brooklyn", "Bklyn", "BK", " Brooklyn ")),
    "Queens": (0.26, 1.05, ("QUEENS", "queens", " Queens", "QN")),
    "Manhattan": (0.20, 0.85, ("MANHATTAN", "manhattan ", "MN", "New York")),
    "Bronx": (0.18, 1.45, ("BRONX", "bronx", "The Bronx", "BX")),
    "Staten Island": (0.06, 1.1, ("STATEN ISLAND", "staten island", "SI", "Staten  Island")),
}

CHANNELS: dict[str, float] = {"Phone": 0.45, "Online": 0.35, "Mobile": 0.20}
HOUR_WEIGHTS = np.array([1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 7, 6, 5, 4, 3, 2], dtype=float)
BAD_DATES: tuple[str, ...] = ("not a date", "2025-13-40 25:00:00", "N/A", "31/02/2025", "")


@dataclass(frozen=True, slots=True)
class MessCounts:
    """How many rows of each kind of mess ``generate_requests`` injects for a given ``n``.

    Attributes:
        duplicates: Extra rows that repeat an existing request ID (exact copies).
        missing_borough: Rows whose borough is blank.
        bad_created: Rows whose ``created_at`` cannot be parsed.
        bad_closed: Closed rows whose ``closed_at`` cannot be parsed.
        closed_before_created: Closed rows whose ``closed_at`` is earlier than ``created_at``.
        outliers: Closed rows with an extreme resolution time (over 1500 hours).
    """

    duplicates: int
    missing_borough: int
    bad_created: int
    bad_closed: int
    closed_before_created: int
    outliers: int


def mess_counts(n: int) -> MessCounts:
    """Return the exact number of messy rows injected for ``n`` requests.

    Args:
        n: Number of distinct requests.

    Returns:
        The injected counts.
    """
    return MessCounts(
        duplicates=n // 50,
        missing_borough=n // 40,
        bad_created=n // 100,
        bad_closed=n // 100,
        closed_before_created=n // 200,
        outliers=n // 200,
    )


def _fmt(ts: np.datetime64) -> str:
    return str(ts.astype("datetime64[s]")).replace("T", " ")


def generate_requests(n: int = 2000, seed: int = 311) -> str:
    """Generate a raw 311 service-request CSV.

    The same ``(n, seed)`` always produces byte-identical output. Rows are shuffled, and the feed contains
    inconsistent casing, missing values, unparseable dates, impossible durations, outliers, and duplicate IDs.

    Args:
        n: Number of distinct requests (before duplicates are added). Must be at least 200.
        seed: Seed for ``numpy.random.default_rng``.

    Returns:
        CSV text with a header row and ``n + n // 50`` data rows.

    Raises:
        ValueError: If ``n`` is below 200.
    """
    if n < 200:
        raise ValueError("n must be at least 200 so every kind of mess appears")
    rng = np.random.default_rng(seed)
    cat_names = list(CATEGORIES)
    cat_p = np.array([CATEGORIES[c][0] for c in cat_names])
    boro_names = list(BOROUGHS)
    boro_p = np.array([BOROUGHS[b][0] for b in boro_names])
    chan_names = list(CHANNELS)
    chan_p = np.array(list(CHANNELS.values()))

    categories = rng.choice(len(cat_names), size=n, p=cat_p / cat_p.sum())
    boroughs = rng.choice(len(boro_names), size=n, p=boro_p / boro_p.sum())
    channels = rng.choice(len(chan_names), size=n, p=chan_p / chan_p.sum())
    days = rng.integers(0, WEEKS * 7, size=n)
    hours = rng.choice(24, size=n, p=HOUR_WEIGHTS / HOUR_WEIGHTS.sum())
    seconds = rng.integers(0, 3600, size=n)
    created = START + (days * 86400 + hours * 3600 + seconds).astype("timedelta64[s]")

    cat_median = np.array([CATEGORIES[c][1] for c in cat_names])
    boro_factor = np.array([BOROUGHS[b][1] for b in boro_names])
    medians = cat_median[categories] * boro_factor[boroughs]
    resolution_hours = medians * rng.lognormal(mean=0.0, sigma=0.8, size=n)
    is_open = rng.random(n) < 0.08

    counts = mess_counts(n)
    closed_pool = rng.permutation(np.flatnonzero(~is_open))
    cuts = np.cumsum([counts.bad_closed, counts.closed_before_created, counts.outliers])
    bad_closed_idx, negative_idx, outlier_idx = np.split(closed_pool[: cuts[-1]], cuts[:-1])
    remaining = rng.permutation(np.setdiff1d(np.arange(n), closed_pool[: cuts[-1]]))
    bad_created_idx = remaining[: counts.bad_created]
    missing_borough_idx = remaining[counts.bad_created : counts.bad_created + counts.missing_borough]

    resolution_hours[outlier_idx] = rng.uniform(1500, 5000, size=len(outlier_idx))
    resolution_hours[negative_idx] = -rng.uniform(1, 48, size=len(negative_idx))
    closed = created + np.round(resolution_hours * 3600).astype("timedelta64[s]")

    messy_casing = rng.random(n) < 0.3
    variant_pick = rng.integers(0, 10, size=n)
    category_style = rng.integers(0, 4, size=n)
    bad_created_pick = rng.integers(0, len(BAD_DATES), size=n)

    missing_borough_set = set(missing_borough_idx.tolist())
    bad_created_set = set(bad_created_idx.tolist())
    bad_closed_set = set(bad_closed_idx.tolist())
    rows: list[list[str]] = []
    for i in range(n):
        canonical = boro_names[boroughs[i]]
        variants = BOROUGHS[canonical][2]
        borough = variants[variant_pick[i] % len(variants)] if messy_casing[i] else canonical
        if i in missing_borough_set:
            borough = ""
        category = cat_names[categories[i]]
        category = (category, category.upper(), category.lower(), f" {category} ")[category_style[i]]
        created_text = _fmt(created[i])
        if i in bad_created_set:
            created_text = BAD_DATES[bad_created_pick[i]]
        closed_text = "" if is_open[i] else _fmt(closed[i])
        if i in bad_closed_set:
            closed_text = "unknown"
        rows.append(
            [
                f"SR-{i + 1:07d}",
                created_text,
                closed_text,
                category,
                borough,
                chan_names[channels[i]],
                "Open" if is_open[i] else "Closed",
            ]
        )
    duplicate_source = rng.choice(n, size=counts.duplicates, replace=False)
    rows.extend(list(rows[i]) for i in duplicate_source)
    order = rng.permutation(len(rows))

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerows(rows[i] for i in order)
    return buffer.getvalue()


def write_requests(path: Path, n: int = 2000, seed: int = 311) -> Path:
    """Write ``generate_requests(n, seed)`` to ``path`` (UTF-8), creating parent directories.

    Args:
        path: Destination CSV file.
        n: Number of distinct requests.
        seed: Random seed.

    Returns:
        The path written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_requests(n, seed), encoding="utf-8")
    return path
