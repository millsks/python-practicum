"""Command-line entry point: ``pixi run python -m crawler https://docs.example.com/``."""

from __future__ import annotations

import argparse
import asyncio  # noqa: F401
import sys  # noqa: F401
from collections.abc import Sequence

from crawler.crawler import Crawler  # noqa: F401
from crawler.fetcher import Fetcher, UrllibFetcher  # noqa: F401
from crawler.models import CrawlConfig  # noqa: F401


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
    # TODO: Parse args, build a CrawlConfig and Crawler, run the crawl under asyncio.timeout with asyncio.run,
    #   print the JSON report, and return 0 (clean), 1 (broken links), or 2 (bad URL / timeout).
    raise NotImplementedError
