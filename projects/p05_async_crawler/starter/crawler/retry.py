"""Retries with capped exponential backoff and full jitter."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from crawler.fetcher import Fetcher, FetchError
from crawler.models import RETRYABLE_STATUSES, Response  # noqa: F401

Sleep = Callable[[float], Awaitable[None]]
TRANSIENT_ERRORS: tuple[type[Exception], ...] = (FetchError, ConnectionError, TimeoutError)


def backoff_ceiling(attempt: int, base: float, cap: float) -> float:
    """Return the largest delay allowed before retry number ``attempt``.

    Args:
        attempt: Zero-based retry number (0 is the first retry).
        base: Ceiling for the first retry, in seconds.
        cap: Upper bound on any ceiling, in seconds.

    Returns:
        ``min(cap, base * 2 ** attempt)``.
    """
    # TODO: min(cap, base * 2 ** attempt) as a float.
    raise NotImplementedError


def backoff_delay(attempt: int, base: float, cap: float, rng: random.Random) -> float:
    """Pick a jittered delay in ``[0, backoff_ceiling(attempt)]`` ("full jitter").

    Jitter spreads retries from many clients over time so they don't hammer a recovering server in lockstep.

    Args:
        attempt: Zero-based retry number.
        base: Ceiling for the first retry, in seconds.
        cap: Upper bound on any ceiling, in seconds.
        rng: Random source, injectable for reproducible tests.

    Returns:
        Seconds to sleep.
    """
    # TODO: Full jitter: rng.uniform(0, ceiling).
    raise NotImplementedError


@dataclass(frozen=True, slots=True)
class FetchOutcome:
    """The result of fetching with retries.

    Attributes:
        response: The final response, or ``None`` if every attempt raised.
        attempts: Number of attempts made.
        error: Description of the last exception when ``response`` is ``None``.
        delays: The backoff delays slept between attempts.
    """

    response: Response | None
    attempts: int
    error: str | None
    delays: tuple[float, ...]


async def fetch_with_retries(
    fetcher: Fetcher,
    url: str,
    *,
    retries: int,
    base: float,
    cap: float,
    rng: random.Random,
    sleep: Sleep = asyncio.sleep,
) -> FetchOutcome:
    """Fetch ``url``, retrying transient failures.

    Transient failures are the exceptions in ``TRANSIENT_ERRORS`` and the statuses in ``RETRYABLE_STATUSES``
    (429 and 5xx gateway errors). Any other status, including 404, is final and returned immediately.

    Args:
        fetcher: Object that performs the request.
        url: URL to fetch.
        retries: Extra attempts after the first.
        base: Backoff ceiling for the first retry.
        cap: Maximum backoff ceiling.
        rng: Random source for jitter.
        sleep: Async sleep function, injectable for tests.

    Returns:
        The final outcome. A retryable status that never recovers is returned as that response.
    """
    # TODO: Loop retries + 1 times. Before every attempt except the first, sleep backoff_delay(attempt - 1, ...).
    #   Catch TRANSIENT_ERRORS (remember the message); stop as soon as a status is not in RETRYABLE_STATUSES.
    #   Return FetchOutcome(response, attempts, error, tuple(delays)).
    raise NotImplementedError
