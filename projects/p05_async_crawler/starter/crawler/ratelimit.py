"""Per-host politeness: a minimum interval between requests to the same host."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable

Sleep = Callable[[float], Awaitable[None]]
Clock = Callable[[], float]


class HostRateLimiter:
    """Space out requests so each host sees at most one request per ``interval`` seconds.

    Different hosts never wait for each other. Callers for the same host queue on a per-host lock,
    so the waits are fair and the interval holds even with many concurrent workers.
    """

    def __init__(
        self,
        interval: float,
        *,
        clock: Clock = time.monotonic,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        """Create a limiter.

        Args:
            interval: Minimum seconds between two requests to one host; ``0`` disables limiting.
            clock: Monotonic time source, injectable for tests.
            sleep: Async sleep function, injectable for tests.

        Raises:
            ValueError: If ``interval`` is negative.
        """
        # TODO: Store interval, clock, sleep; keep dicts for the last request time, a Lock, and an override per host.
        raise NotImplementedError

    def set_interval(self, host: str, interval: float) -> None:
        """Override the interval for one host, for example from a robots.txt ``Crawl-delay``.

        Args:
            host: Host name.
            interval: Minimum seconds between requests to ``host``.
        """
        # TODO: Store a per-host override (never below 0).
        raise NotImplementedError

    def interval_for(self, host: str) -> float:
        """Return the interval in force for ``host``.

        Args:
            host: Host name.

        Returns:
            Seconds between requests.
        """
        # TODO: Return the override for host, else the default interval.
        raise NotImplementedError

    async def acquire(self, host: str) -> float:
        """Wait until a request to ``host`` is allowed, then claim the slot.

        Args:
            host: Host name.

        Returns:
            Seconds this call waited.
        """
        # TODO: Interval 0 -> return 0.0 immediately.
        #   Otherwise hold the host's asyncio.Lock, sleep for last + interval - now (if positive),
        #   record clock() as the host's last request time, and return how long you waited.
        raise NotImplementedError
