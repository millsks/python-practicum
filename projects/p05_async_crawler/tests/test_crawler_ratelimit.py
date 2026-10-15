"""Milestone 3: per-host rate limiting."""

import asyncio

import pytest
from crawler.ratelimit import HostRateLimiter


class FakeTime:
    """A virtual clock whose sleep advances time instantly."""

    def __init__(self) -> None:
        """Start the clock at zero."""
        self.now = 0.0

    def clock(self) -> float:
        """Return the virtual time."""
        return self.now

    async def sleep(self, delay: float) -> None:
        """Advance virtual time by ``delay`` and yield to the loop."""
        self.now += delay
        await asyncio.sleep(0)


def test_requests_to_one_host_are_spaced_by_the_interval() -> None:
    time = FakeTime()
    limiter = HostRateLimiter(2.0, clock=time.clock, sleep=time.sleep)

    async def main() -> list[float]:
        stamps = []
        for _ in range(3):
            await limiter.acquire("a.com")
            stamps.append(time.now)
        return stamps

    assert asyncio.run(main()) == [0.0, 2.0, 4.0], "three sequential requests should start at t=0, 2, 4"


def test_concurrent_callers_for_one_host_are_serialized() -> None:
    time = FakeTime()
    limiter = HostRateLimiter(1.0, clock=time.clock, sleep=time.sleep)

    async def main() -> list[float]:
        stamps: list[float] = []

        async def one() -> None:
            await limiter.acquire("a.com")
            stamps.append(time.now)

        async with asyncio.TaskGroup() as group:
            for _ in range(4):
                group.create_task(one())
        return stamps

    assert asyncio.run(main()) == [0.0, 1.0, 2.0, 3.0], "concurrent callers must still be one interval apart"


def test_different_hosts_do_not_wait_for_each_other() -> None:
    time = FakeTime()
    limiter = HostRateLimiter(5.0, clock=time.clock, sleep=time.sleep)

    async def main() -> list[float]:
        return [await limiter.acquire(host) for host in ("a.com", "b.com", "c.com")]

    assert asyncio.run(main()) == [0.0, 0.0, 0.0], "the first request to each host never waits"


def test_per_host_override_and_zero_interval() -> None:
    time = FakeTime()
    limiter = HostRateLimiter(0.0, clock=time.clock, sleep=time.sleep)
    limiter.set_interval("slow.com", 3.0)

    async def main() -> tuple[float, float]:
        await limiter.acquire("fast.com")
        fast = await limiter.acquire("fast.com")
        await limiter.acquire("slow.com")
        slow = await limiter.acquire("slow.com")
        return fast, slow

    assert asyncio.run(main()) == (0.0, 3.0), "interval 0 never waits; the override makes slow.com wait 3s"
    assert limiter.interval_for("slow.com") == 3.0 and limiter.interval_for("other") == 0.0, "interval_for works"


def test_negative_interval_is_rejected() -> None:
    with pytest.raises(ValueError, match="interval"):
        HostRateLimiter(-1.0)
