"""Milestones 4 and 5: the concurrent crawl engine, shutdown, and cancellation."""

import asyncio

import pytest
from crawler.crawler import Crawler, crawl
from crawler.fetcher import FakeFetcher, FetchError, html_response, redirect_response
from crawler.models import CrawlConfig, Response

BASE = "https://docs.example.com"


async def no_sleep(delay: float) -> None:
    await asyncio.sleep(0)


def page(*hrefs: str) -> Response:
    return html_response("".join(f'<a href="{href}">{href}</a>' for href in hrefs))


def docs_site() -> dict[str, object]:
    return {
        f"{BASE}/robots.txt": Response(200, {}, "User-agent: *\nDisallow: /private/\n"),
        f"{BASE}/": page(
            "/guide/", "/api/", "/missing", "/old", "/private/secret", "https://other.org/x", "mailto:a@b"
        ),
        f"{BASE}/guide/": page("install", "/api/", "../"),
        f"{BASE}/guide/install": page("/guide/deep/"),
        f"{BASE}/guide/deep/": page("/guide/deeper"),
        f"{BASE}/api/": page("/api/flaky", "/missing"),
        f"{BASE}/api/flaky": [FetchError("reset"), html_response("<p>ok</p>")],
        f"{BASE}/old": redirect_response("/guide/"),
    }


def run(fetcher: FakeFetcher, config: CrawlConfig | None = None, start: str = f"{BASE}/"):
    return asyncio.run(crawl(start, fetcher, config or CrawlConfig(max_depth=2), sleep=no_sleep))


def test_crawls_the_site_and_reports_broken_links_with_referrers() -> None:
    report = run(FakeFetcher(docs_site()))
    broken = {link.url: link for link in report.broken}
    assert list(broken) == [f"{BASE}/missing"], f"only /missing is broken, got {list(broken)}"
    assert broken[f"{BASE}/missing"].status == 404, "a missing page reports its 404"
    assert broken[f"{BASE}/missing"].referrers == (f"{BASE}/", f"{BASE}/api/"), "every referrer is listed, sorted"


def test_each_url_is_fetched_once() -> None:
    fetcher = FakeFetcher(docs_site())
    run(fetcher)
    for url in (f"{BASE}/", f"{BASE}/guide/", f"{BASE}/api/", f"{BASE}/missing"):
        assert fetcher.count(url) == 1, f"{url} is linked from several pages but must be fetched once"


def test_robots_txt_is_fetched_once_and_obeyed() -> None:
    fetcher = FakeFetcher(docs_site())
    report = run(fetcher)
    assert fetcher.count(f"{BASE}/robots.txt") == 1, "robots.txt should be fetched once per host and cached"
    assert report.blocked == (f"{BASE}/private/secret",), "the disallowed URL is reported as blocked"
    assert f"{BASE}/private/secret" not in fetcher.calls, "a disallowed URL must never be fetched"


def test_robots_can_be_ignored() -> None:
    fetcher = FakeFetcher(docs_site())
    report = run(fetcher, CrawlConfig(max_depth=1, respect_robots=False))
    assert f"{BASE}/robots.txt" not in fetcher.calls, "respect_robots=False skips robots.txt"
    assert report.blocked == (), "nothing is blocked when robots are ignored"
    assert f"{BASE}/private/secret" in fetcher.calls, "the private page is crawled when robots are ignored"


def test_external_links_are_recorded_but_not_fetched() -> None:
    fetcher = FakeFetcher(docs_site())
    report = run(fetcher)
    assert report.external == ("https://other.org/x",), "off-site links are listed as external"
    assert "https://other.org/x" not in fetcher.calls, "off-site links are never fetched"


def test_redirects_are_reported_and_followed_once() -> None:
    fetcher = FakeFetcher(docs_site())
    report = run(fetcher)
    assert [(r.source, r.target, r.status) for r in report.redirects] == [(f"{BASE}/old", f"{BASE}/guide/", 301)], (
        "the redirect from /old to /guide/ should be reported with its status"
    )
    assert fetcher.count(f"{BASE}/guide/") == 1, "the redirect target was already queued and must not be refetched"


def test_retries_rescue_a_flaky_page() -> None:
    report = run(FakeFetcher(docs_site()))
    flaky = next(p for p in report.pages if p.url == f"{BASE}/api/flaky")
    assert flaky.status == 200 and flaky.attempts == 2, "the flaky page fails once, then succeeds on retry"


def test_permanent_network_failure_is_broken_with_error() -> None:
    site = docs_site() | {f"{BASE}/api/flaky": FetchError("connection refused")}
    report = run(FakeFetcher(site), CrawlConfig(max_depth=2, retries=1))
    broken = {link.url: link for link in report.broken}
    assert broken[f"{BASE}/api/flaky"].status is None, "a page that never answered has no status"
    assert broken[f"{BASE}/api/flaky"].error == "connection refused", "the network error is reported"
    assert broken[f"{BASE}/api/flaky"].referrers == (f"{BASE}/api/",), "the referrer is kept for network failures"


def test_max_depth_limits_how_far_links_are_followed() -> None:
    fetcher = FakeFetcher(docs_site())
    report = run(fetcher, CrawlConfig(max_depth=1))
    assert f"{BASE}/guide/install" not in fetcher.calls, "depth-2 pages must not be fetched when max_depth=1"
    assert max(p.depth for p in report.pages) == 1, "no fetched page is deeper than max_depth"
    deep = run(FakeFetcher(docs_site()), CrawlConfig(max_depth=3))
    assert deep.depth_counts[3] == 1 and deep.max_depth_reached == 3, "with max_depth=3 one page is at depth 3"


def test_depth_zero_fetches_only_the_start_page() -> None:
    report = run(FakeFetcher(docs_site()), CrawlConfig(max_depth=0))
    assert [p.url for p in report.pages] == [f"{BASE}/"], "max_depth=0 crawls only the start URL"


def test_max_pages_caps_the_crawl_and_marks_truncation() -> None:
    fetcher = FakeFetcher(docs_site())
    report = run(fetcher, CrawlConfig(max_depth=5, max_pages=3))
    fetched = [url for url in fetcher.calls if not url.endswith("robots.txt")]
    assert len(fetched) == 3, f"only 3 pages may be fetched, got {fetched}"
    assert report.truncated, "the report should say the page budget ran out"


def test_concurrency_is_bounded_and_actually_concurrent() -> None:
    links = [f"/p{i}" for i in range(12)]
    site = {f"{BASE}/": page(*links)} | {f"{BASE}{link}": page() for link in links}
    fetcher = FakeFetcher(site, latency=0.01)
    asyncio.run(crawl(f"{BASE}/", fetcher, CrawlConfig(concurrency=3, respect_robots=False)))
    assert fetcher.max_in_flight == 3, f"exactly 3 workers should be fetching at peak, saw {fetcher.max_in_flight}"


def test_per_host_interval_spaces_requests() -> None:
    delays: list[float] = []

    async def recording_sleep(delay: float) -> None:
        delays.append(delay)
        await asyncio.sleep(0)

    site = {f"{BASE}/": page("/a", "/b")}
    config = CrawlConfig(per_host_interval=0.5, respect_robots=False, concurrency=2)
    report = asyncio.run(crawl(f"{BASE}/", FakeFetcher(site), config, sleep=recording_sleep))
    assert len(report.pages) == 3, "three pages are crawled"
    assert len(delays) >= 2 and all(d > 0 for d in delays), f"later requests to the host must wait: {delays}"


def test_crawl_delay_from_robots_raises_the_interval() -> None:
    delays: list[float] = []

    async def recording_sleep(delay: float) -> None:
        delays.append(delay)
        await asyncio.sleep(0)

    site = {f"{BASE}/robots.txt": Response(200, {}, "User-agent: *\nCrawl-delay: 30\n"), f"{BASE}/": page("/a")}
    asyncio.run(crawl(f"{BASE}/", FakeFetcher(site), CrawlConfig(concurrency=1), sleep=recording_sleep))
    assert delays and max(delays) > 20, f"a 30s Crawl-delay should make the crawler wait about 30s: {delays}"


def test_non_html_pages_are_not_parsed() -> None:
    site = {f"{BASE}/": Response(200, {"Content-Type": "application/json"}, '<a href="/hidden">x</a>')}
    fetcher = FakeFetcher(site)
    asyncio.run(crawl(f"{BASE}/", fetcher, CrawlConfig(respect_robots=False), sleep=no_sleep))
    assert fetcher.calls == [f"{BASE}/"], "links inside a non-HTML body must not be followed"


def test_invalid_start_url_raises() -> None:
    with pytest.raises(ValueError, match="not a crawlable URL"):
        asyncio.run(crawl("ftp://example.com/", FakeFetcher({})))


def test_cancellation_leaves_no_running_tasks_and_keeps_a_partial_report() -> None:
    links = [f"/slow{i}" for i in range(20)]
    site = {f"{BASE}/": page(*links)} | {f"{BASE}{link}": page() for link in links}
    fetcher = FakeFetcher(site, latency={f"{BASE}{link}": 10.0 for link in links})
    crawler = Crawler(fetcher, CrawlConfig(concurrency=4, respect_robots=False))

    async def main() -> set[asyncio.Task[object]]:
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.05):
                await crawler.crawl(f"{BASE}/")
        return {t for t in asyncio.all_tasks() if t is not asyncio.current_task()}

    leftover = asyncio.run(main())
    assert leftover == set(), f"every worker must be cancelled and awaited, found {leftover}"
    assert fetcher.in_flight == 0, "in-flight requests must be cleaned up on cancellation"
    assert crawler.in_progress == set(), "the crawler must forget in-progress URLs after cancellation"
    partial = crawler.report()
    assert [p.url for p in partial.pages] == [f"{BASE}/"], "the start page finished before the timeout"


def test_worker_crash_propagates_as_exception_group() -> None:
    class Exploding(FakeFetcher):
        async def fetch(self, url: str) -> Response:
            if url.endswith("/boom"):
                raise RuntimeError("bug in fetcher")
            return await super().fetch(url)

    fetcher = Exploding({f"{BASE}/": page("/boom", "/a", "/b")})
    with pytest.raises(ExceptionGroup) as info:
        asyncio.run(crawl(f"{BASE}/", fetcher, CrawlConfig(respect_robots=False)))
    assert info.group_contains(RuntimeError, match="bug in fetcher"), "a non-transient bug must not be swallowed"


def test_crawler_can_be_reused_for_a_second_crawl() -> None:
    crawler = Crawler(FakeFetcher(docs_site()), CrawlConfig(max_depth=0), sleep=no_sleep)
    first = asyncio.run(crawler.crawl(f"{BASE}/"))
    second = asyncio.run(crawler.crawl(f"{BASE}/guide/"))
    assert [p.url for p in first.pages] == [f"{BASE}/"], "first crawl sees only its start page"
    assert [p.url for p in second.pages] == [f"{BASE}/guide/"], "state must reset between crawls"
