"""The crawl engine: an ``asyncio.Queue`` feeding a bounded pool of workers inside a ``TaskGroup``."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

from crawler.fetcher import Fetcher
from crawler.links import extract_links
from crawler.models import CrawlConfig, PageResult, Redirect
from crawler.ratelimit import HostRateLimiter, Sleep
from crawler.report import CrawlReport, build_report
from crawler.retry import FetchOutcome, fetch_with_retries
from crawler.robots import RobotsPolicy
from crawler.urls import host_of, normalize_url, robots_url, same_site


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
        self.fetcher = fetcher
        self.config = config or CrawlConfig()
        self._sleep = sleep
        self._rng = rng or random.Random(0)
        self._limiter = limiter or HostRateLimiter(self.config.per_host_interval, sleep=sleep)
        self._reset("")

    def _reset(self, start_url: str) -> None:
        self._start = start_url
        self._seen: set[str] = set()
        self._referrers: dict[str, set[str]] = {}
        self._results: dict[str, PageResult] = {}
        self._redirects: list[Redirect] = []
        self._blocked: set[str] = set()
        self._external: set[str] = set()
        self._truncated = False
        self._policies: dict[str, RobotsPolicy] = {}
        self._policy_locks: dict[str, asyncio.Lock] = {}
        self.in_progress: set[str] = set()

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
        start = normalize_url(start_url)
        if start is None:
            raise ValueError(f"not a crawlable URL: {start_url!r}")
        self._reset(start)
        queue: asyncio.Queue[Job | None] = asyncio.Queue()
        self._schedule(queue, Job(start, 0, None))
        async with asyncio.TaskGroup() as group:
            for index in range(self.config.concurrency):
                group.create_task(self._worker(queue), name=f"crawler-worker-{index}")
            await queue.join()
            for _ in range(self.config.concurrency):
                queue.put_nowait(None)
        return self.report()

    def report(self) -> CrawlReport:
        """Build a report from everything collected so far (also usable after a cancelled crawl).

        Returns:
            The report.
        """
        return build_report(
            self._start,
            self._results.values(),
            self._referrers,
            self._redirects,
            self._blocked,
            self._external,
            truncated=self._truncated,
        )

    def _schedule(self, queue: asyncio.Queue[Job | None], job: Job) -> None:
        if job.referrer is not None:
            self._referrers.setdefault(job.url, set()).add(job.referrer)
        if job.url in self._seen:
            return
        if len(self._seen) >= self.config.max_pages:
            self._truncated = True
            return
        self._seen.add(job.url)
        queue.put_nowait(job)

    def _discovered(self, queue: asyncio.Queue[Job | None], url: str, depth: int, referrer: str) -> None:
        if same_site(url, self._start, allow_subdomains=self.config.allow_subdomains):
            self._schedule(queue, Job(url, depth, referrer))
        else:
            self._external.add(url)

    async def _worker(self, queue: asyncio.Queue[Job | None]) -> None:
        while True:
            job = await queue.get()
            try:
                if job is None:
                    return
                self.in_progress.add(job.url)
                try:
                    await self._process(queue, job)
                finally:
                    self.in_progress.discard(job.url)
            finally:
                queue.task_done()

    async def _policy(self, url: str) -> RobotsPolicy:
        host = host_of(url)
        if not self.config.respect_robots:
            return RobotsPolicy.allow_all(self.config.user_agent)
        lock = self._policy_locks.setdefault(host, asyncio.Lock())
        async with lock:
            if host not in self._policies:
                await self._limiter.acquire(host)
                outcome = await self._fetch(robots_url(url))
                policy = RobotsPolicy.from_response(outcome.response, self.config.user_agent)
                delay = policy.crawl_delay()
                if delay > self._limiter.interval_for(host):
                    self._limiter.set_interval(host, delay)
                self._policies[host] = policy
            return self._policies[host]

    async def _fetch(self, url: str) -> FetchOutcome:
        return await fetch_with_retries(
            self.fetcher,
            url,
            retries=self.config.retries,
            base=self.config.backoff_base,
            cap=self.config.backoff_cap,
            rng=self._rng,
            sleep=self._sleep,
        )

    async def _process(self, queue: asyncio.Queue[Job | None], job: Job) -> None:
        if not (await self._policy(job.url)).allowed(job.url):
            self._blocked.add(job.url)
            return
        await self._limiter.acquire(host_of(job.url))
        outcome = await self._fetch(job.url)
        response = outcome.response
        links: list[str] = []
        if response is not None and response.is_redirect:
            target = normalize_url(response.header("location"), job.url)
            if target is not None:
                self._redirects.append(Redirect(job.url, target, response.status))
                self._discovered(queue, target, job.depth, job.url)
        elif response is not None and response.status < 400 and response.is_html:
            links = extract_links(response.body, job.url)
            if job.depth < self.config.max_depth:
                for link in links:
                    self._discovered(queue, link, job.depth + 1, job.url)
        self._results[job.url] = PageResult(
            url=job.url,
            depth=job.depth,
            status=None if response is None else response.status,
            attempts=outcome.attempts,
            error=outcome.error,
            links=tuple(links),
        )


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
    return await Crawler(fetcher, config, sleep=sleep, rng=rng).crawl(start_url)
