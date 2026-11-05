"""Settings read from the environment."""

import os


def load_config() -> dict[str, object]:
    """Read the currency and tax rate from the environment.

    Returns:
        A mapping with ``currency`` (upper case) and ``tax`` (a float from 0 up to, but not including, 1).

    Raises:
        ValueError: If ``INVOICER_TAX`` is not a number or is out of range.
    """
    currency = os.environ.get("INVOICER_CURRENCY", "USD").upper()
    try:
        tax = float(os.environ.get("INVOICER_TAX", "0.2"))
    except ValueError:
        raise ValueError("INVOICER_TAX must be a number") from None
    if not 0 <= tax < 1:
        raise ValueError("INVOICER_TAX must be at least 0 and below 1")
    return {"currency": currency, "tax": tax}
