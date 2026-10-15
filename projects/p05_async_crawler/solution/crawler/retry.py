"""Retries with capped exponential backoff and full jitter."""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from crawler.fetcher import Fetcher, FetchError
from crawler.models import RETRYABLE_STATUSES, Response

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
    return float(min(cap, base * 2.0**attempt))


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
    return rng.uniform(0.0, backoff_ceiling(attempt, base, cap))


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
    delays: list[float] = []
    response: Response | None = None
    error: str | None = None
    attempts = 0
    for attempt in range(retries + 1):
        if attempt:
            delay = backoff_delay(attempt - 1, base, cap, rng)
            delays.append(delay)
            await sleep(delay)
        attempts += 1
        try:
            response = await fetcher.fetch(url)
        except TRANSIENT_ERRORS as exc:
            response, error = None, str(exc) or type(exc).__name__
            continue
        error = None
        if response.status not in RETRYABLE_STATUSES:
            break
    return FetchOutcome(response, attempts, error, tuple(delays))
