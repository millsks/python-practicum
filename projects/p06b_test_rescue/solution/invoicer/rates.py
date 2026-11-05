"""Exchange rates from a remote service."""

import json
import time
import urllib.error
import urllib.request

URL = "https://rates.example.test/latest?symbol={currency}"


class RateError(RuntimeError):
    """The rate service could not be reached."""


def fetch_rate(currency: str, retries: int = 3) -> float:
    """Fetch the rate from USD to ``currency``, retrying with exponential backoff.

    Args:
        currency: Currency code to look up.
        retries: Total number of attempts.

    Returns:
        The exchange rate.

    Raises:
        RateError: If every attempt fails.
    """
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(URL.format(currency=currency), timeout=5) as response:
                return float(json.load(response)["rate"])
        except urllib.error.URLError:
            if attempt == retries - 1:
                raise RateError(f"could not fetch {currency}") from None
            time.sleep(2**attempt)
    raise RateError(f"could not fetch {currency}")
