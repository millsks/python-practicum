"""Load the raw 311 CSV with explicit, predictable dtypes."""

from pathlib import Path

import pandas as pd

from cityeda.generate import COLUMNS

RAW_DTYPES: dict[str, str] = {
    "request_id": "str",
    "created_at": "str",
    "closed_at": "str",
    "category": "str",
    "borough": "str",
    "channel": "category",
    "status": "category",
}


def load_requests(path: Path) -> pd.DataFrame:
    """Read a raw service-request CSV without letting pandas guess types.

    Dates stay as text here: parsing them is a cleaning rule with its own log entry. Blank fields become missing
    values. Columns come back in the order of ``COLUMNS``.

    Args:
        path: CSV file produced by ``generate_requests`` or the city's export.

    Returns:
        The raw frame with the dtypes in ``RAW_DTYPES``.

    Raises:
        ValueError: If any expected column is missing from the file.
    """
    header = pd.read_csv(path, nrows=0).columns
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        raise ValueError(f"{path} is missing columns: {', '.join(missing)}")
    return pd.read_csv(path, usecols=list(COLUMNS), dtype=RAW_DTYPES)[list(COLUMNS)]
