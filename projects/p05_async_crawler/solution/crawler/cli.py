"""Command-line entry point: ``pixi run python -m crawler https://docs.example.com/``."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

from crawler.crawler import Crawler
from crawler.fetcher import Fetcher, UrllibFetcher
from crawler.models import CrawlConfig


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        The parser.
    """
    parser = argparse.ArgumentParser(prog="crawler", description="Find broken links on one site.")
    parser.add_argument("url", help="start URL, for example https://docs.example.com/")
    parser.add_argument("--max-depth", type=int, default=3, help="deepest link level to fetch (default 3)")
    parser.add_argument("--max-pages", type=int, default=200, help="page budget (default 200)")
    parser.add_argument("--concurrency", type=int, default=4, help="parallel workers (default 4)")
    parser.add_argument("--interval", type=float, default=0.5, help="seconds between requests per host")
    parser.add_argument("--retries", type=int, default=2, help="retries for transient failures")
    parser.add_argument("--ignore-robots", action="store_true", help="do not fetch or obey robots.txt")
    parser.add_argument("--timeout", type=float, default=300.0, help="overall crawl timeout in seconds")
    return parser


def main(argv: Sequence[str] | None = None, *, fetcher: Fetcher | None = None) -> int:
    """Run a crawl and print the JSON report.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.
        fetcher: Fetcher to use; defaults to :class:`UrllibFetcher` (tests inject a fake).

    Returns:
        ``0`` when no broken links were found, ``1`` when some were, ``2`` on a timeout or bad URL.
    """
    args = build_parser().parse_args(argv)
    config = CrawlConfig(
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        concurrency=args.concurrency,
        per_host_interval=args.interval,
        retries=args.retries,
        respect_robots=not args.ignore_robots,
    )
    crawler = Crawler(fetcher or UrllibFetcher(), config)

    async def run() -> None:
        async with asyncio.timeout(args.timeout):
            await crawler.crawl(args.url)

    try:
        asyncio.run(run())
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except TimeoutError:
        print("error: crawl timed out; partial report follows", file=sys.stderr)
        print(crawler.report().to_json())
        return 2
    report = crawler.report()
    print(report.to_json())
    return 1 if report.broken else 0
