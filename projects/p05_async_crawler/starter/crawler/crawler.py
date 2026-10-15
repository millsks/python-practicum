"""The crawl engine: an ``asyncio.Queue`` feeding a bounded pool of workers inside a ``TaskGroup``."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

from crawler.fetcher import Fetcher
from crawler.links import extract_links  # noqa: F401
from crawler.models import CrawlConfig, PageResult, Redirect  # noqa: F401
from crawler.ratelimit import HostRateLimiter, Sleep
from crawler.report import CrawlReport, build_report  # noqa: F401
from crawler.retry import FetchOutcome, fetch_with_retries  # noqa: F401
from crawler.robots import RobotsPolicy
from crawler.urls import host_of, normalize_url, robots_url, same_site  # noqa: F401


@dataclass(frozen=True, slots=True)
class Job:
    """One unit of work on the queue.

    Attributes:
        url: Normalized URL to fetch.
        depth: Link distance from the start URL.
        referrer: Page that linked here, or ``None`` for the start URL.
    """

    url: str
    depth: int
    referrer: str | None


class Crawler:
    """Crawl one site breadth-first and collect a broken-link report.

    Concurrency is bounded by the number of worker tasks (``config.concurrency``); each host is additionally
    rate-limited. All I/O goes through the injected :class:`~crawler.fetcher.Fetcher`, and all waiting goes
    through the injected ``sleep``, so tests run offline and fast.

    Attributes:
        fetcher: The injected fetcher.
        config: Crawl settings.
        in_progress: URLs currently being processed by a worker.
    """

    def __init__(
        self,
        fetcher: Fetcher,
        config: CrawlConfig | None = None,
        *,
        sleep: Sleep = asyncio.sleep,
        rng: random.Random | None = None,
        limiter: HostRateLimiter | None = None,
    ) -> None:
        """Create a crawler.

        Args:
            fetcher: Performs every request.
            config: Crawl settings; defaults to :class:`CrawlConfig()`.
            sleep: Async sleep for backoff (and the default limiter), injectable for tests.
            rng: Random source for retry jitter; seeded for reproducibility when omitted.
            limiter: Per-host rate limiter; built from ``config.per_host_interval`` when omitted.
        """
        # TODO: Store fetcher, config (default CrawlConfig()), sleep, rng (default random.Random(0)) and a limiter
        #   (default HostRateLimiter(config.per_host_interval, sleep=sleep)); then call self._reset('').
        raise NotImplementedError

    def _reset(self, start_url: str) -> None:
        # TODO: Create fresh crawl state: seen set, referrers dict[str, set[str]], results dict, redirects list,
        #   blocked and external sets, truncated flag, robots policy cache + per-host locks, in_progress set.
        raise NotImplementedError

    async def crawl(self, start_url: str) -> CrawlReport:
        """Crawl from ``start_url`` until the queue drains or the page budget is spent.

        Workers run inside an :class:`asyncio.TaskGroup`. When the queue is fully processed, one ``None``
        sentinel per worker tells each to exit, so the group closes cleanly. If a worker crashes, or the caller
        cancels the crawl (for example with :func:`asyncio.timeout`), the group cancels every other worker and
        waits for them before propagating, so no task outlives the call.

        Args:
            start_url: Where to begin; must be an absolute HTTP(S) URL.

        Returns:
            The report.

        Raises:
            ValueError: If ``start_url`` is not a crawlable URL.
        """
        # TODO: normalize the start URL (ValueError if None), reset, make a Queue, schedule Job(start, 0, None).
        #   Inside `async with asyncio.TaskGroup()`: create config.concurrency worker tasks, await queue.join(),
        #   then put one None sentinel per worker so they exit. Return self.report().
        raise NotImplementedError

    def report(self) -> CrawlReport:
        """Build a report from everything collected so far (also usable after a cancelled crawl).

        Returns:
            The report.
        """
        # TODO: Call build_report with the collected state.
        raise NotImplementedError

    def _schedule(self, queue: asyncio.Queue[Job | None], job: Job) -> None:
        # TODO: Always record the referrer. Skip URLs already seen. When len(seen) >= max_pages set truncated
        #   and skip. Otherwise add to seen and put_nowait the job.
        raise NotImplementedError

    def _discovered(self, queue: asyncio.Queue[Job | None], url: str, depth: int, referrer: str) -> None:
        # TODO: Same-site URLs are scheduled; everything else goes into the external set.
        raise NotImplementedError

    async def _worker(self, queue: asyncio.Queue[Job | None]) -> None:
        # TODO: Loop: job = await queue.get(); in try/finally call queue.task_done() for EVERY item (also None).
        #   None means exit. Track job.url in self.in_progress while processing (discard it in a finally).
        raise NotImplementedError

    async def _policy(self, url: str) -> RobotsPolicy:
        # TODO: Cache one RobotsPolicy per host, guarded by a per-host asyncio.Lock so robots.txt is fetched once.
        #   Respect the limiter for the robots request too, and raise the host interval to the Crawl-delay.
        raise NotImplementedError

    async def _fetch(self, url: str) -> FetchOutcome:
        # TODO: Call fetch_with_retries with the config's retry settings, rng, and sleep.
        raise NotImplementedError

    async def _process(self, queue: asyncio.Queue[Job | None], job: Job) -> None:
        # TODO: Blocked by robots -> record and return. Otherwise acquire the limiter, fetch with retries, then:
        #   redirect -> record Redirect and discover the target at the SAME depth;
        #   HTML with status < 400 -> extract links and discover them at depth + 1 if depth < max_depth.
        #   Finally store a PageResult for the URL.
        raise NotImplementedError


async def crawl(
    start_url: str,
    fetcher: Fetcher,
    config: CrawlConfig | None = None,
    *,
    sleep: Sleep = asyncio.sleep,
    rng: random.Random | None = None,
) -> CrawlReport:
    """Crawl a site with a fresh :class:`Crawler`; a convenience wrapper.

    Args:
        start_url: Absolute start URL.
        fetcher: Performs every request.
        config: Crawl settings.
        sleep: Async sleep for backoff and rate limiting.
        rng: Random source for retry jitter.

    Returns:
        The report.
    """
    # TODO: Build a Crawler and await its crawl().
    raise NotImplementedError
