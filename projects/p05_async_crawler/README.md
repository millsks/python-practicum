# Project 5: Async Web Crawler

Closes Part 5 (Advanced Python). Course page: `docs/projects/p05-async-crawler.html`.

## Scenario

Your team's documentation site has grown to hundreds of pages, and readers keep reporting dead links. You will build
`crawler`, an asyncio crawler that walks one site breadth-first, obeys `robots.txt`, stays polite with per-host rate
limiting, survives flaky servers with retries, and produces a JSON report of every broken link and the pages that
link to it, so writers know exactly what to fix.

The crawler never talks to the network directly. It receives a `Fetcher` (a `typing.Protocol` with one method,
`async def fetch(url) -> Response`). Tests inject `FakeFetcher`, an in-memory site with scripted latency and failures,
so the whole test suite runs offline in well under a second. `UrllibFetcher` is the real fetcher: blocking `urllib`
run in a worker thread with `asyncio.to_thread`.

## Getting started

```bash
pixi run start p05        # copies starter/ into work/p05_async_crawler/
pixi run grade p05        # runs the tests against your work/ copy
pixi run practicum grade p05 -k urls -x   # one milestone only, stop at the first failure
```

Run it for real (after the tests pass) against a site you own or have permission to crawl:

```bash
cd work/p05_async_crawler
pixi run python -m crawler https://docs.example.com/ --max-depth 2 --interval 1.0
```

## What is provided

- `models.py`: `Response`, `CrawlConfig`, `PageResult`, `BrokenLink`, `Redirect` (complete).
- `fetcher.py`: the `Fetcher` Protocol, `FetchError`, `FakeFetcher`, and the `html_response`/`redirect_response`
  helpers (complete); `UrllibFetcher` is yours to finish.

Everything else raises `NotImplementedError` with `TODO` comments.

## Requirements and milestones

1. **URLs and links** (`urls.py`, `links.py`): `normalize_url` (resolve relative links, lowercase scheme and host,
   drop default ports and fragments, remove dot segments, reject `mailto:` and friends), `same_site`, `robots_url`,
   and `extract_links` using `html.parser` (honor `<base href>`, skip `rel="nofollow"`).
2. **robots.txt** (`robots.py`): `RobotsPolicy` over `urllib.robotparser`; a missing file allows everything.
3. **Politeness and resilience** (`ratelimit.py`, `retry.py`): `HostRateLimiter` with an injectable clock and sleep;
   `fetch_with_retries` with capped exponential backoff and full jitter, retrying `FetchError`, 429, and 5xx.
4. **The engine** (`crawler.py`): an `asyncio.Queue` of `Job`s, `config.concurrency` workers in a `TaskGroup`,
   de-duplication, `max_depth`, `max_pages`, redirects, external links, robots blocking.
5. **Shutdown and cancellation**: sentinel-based clean shutdown; cancelling the crawl (for example with
   `asyncio.timeout`) leaves no running tasks, no in-flight requests, and a usable partial `report()`.
6. **Report and CLI** (`report.py`, `cli.py`): JSON report with summary, broken links and referrers, redirects,
   depth counts; exit codes 0 (clean), 1 (broken links), 2 (bad URL or timeout).

## Grading

`pixi run grade p05` runs 81 tests in `tests/`. All must pass.

## Stretch goals

- Check external links with a `HEAD`-style fetch (without crawling them).
- Honor `<meta name="robots" content="nofollow">` and `Retry-After` headers on 429/503.
- An `httpx.AsyncClient`-based fetcher (`pixi add httpx`) and a comparison of thread-backed vs native async I/O.
- Persist the frontier to SQLite so an interrupted crawl can resume.
- Emit structured progress logs with `structlog` (Part 6).
