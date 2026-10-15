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
        if interval < 0:
            raise ValueError("interval must be >= 0")
        self.interval = interval
        self._clock = clock
        self._sleep = sleep
        self._last: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._intervals: dict[str, float] = {}

    def set_interval(self, host: str, interval: float) -> None:
        """Override the interval for one host, for example from a robots.txt ``Crawl-delay``.

        Args:
            host: Host name.
            interval: Minimum seconds between requests to ``host``.
        """
        self._intervals[host] = max(0.0, interval)

    def interval_for(self, host: str) -> float:
        """Return the interval in force for ``host``.

        Args:
            host: Host name.

        Returns:
            Seconds between requests.
        """
        return self._intervals.get(host, self.interval)

    async def acquire(self, host: str) -> float:
        """Wait until a request to ``host`` is allowed, then claim the slot.

        Args:
            host: Host name.

        Returns:
            Seconds this call waited.
        """
        interval = self.interval_for(host)
        if interval <= 0:
            return 0.0
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            waited = 0.0
            last = self._last.get(host)
            if last is not None:
                waited = max(0.0, last + interval - self._clock())
                if waited > 0:
                    await self._sleep(waited)
            self._last[host] = self._clock()
            return waited
