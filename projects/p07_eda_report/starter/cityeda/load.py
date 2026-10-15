"""Load the raw 311 CSV with explicit, predictable dtypes."""

from pathlib import Path

import pandas as pd

from cityeda.generate import COLUMNS

# TODO: refine these dtypes. Every column starts as text; keep dates as text ("str") for now: parsing them is a
# cleaning rule. Low-cardinality text columns (channel, status) are good candidates for "category".
RAW_DTYPES: dict[str, str] = dict.fromkeys(COLUMNS, "str")


def load_requests(path: Path) -> pd.DataFrame:
    """Read a raw service-request CSV without letting pandas guess types.

    Dates stay as text here: parsing them is a cleaning rule with its own log entry. Blank fields become missing
    values. Columns come back in the order of ``COLUMNS``.

    Args:
        path: CSV file produced by ``generate_requests`` or the city's export.

    Returns:
        The raw frame with the dtypes in ``RAW_DTYPES``.

    Raises:
        ValueError: If any expected column is missing from the file (message contains "missing columns").
    """
    # TODO: read only the header first (nrows=0) and raise ValueError listing any missing columns.
    # TODO: read the file with usecols=list(COLUMNS) and dtype=RAW_DTYPES, then reorder to COLUMNS.
    raise NotImplementedError
