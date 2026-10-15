"""Turn raw crawl results into a broken-link report that serializes to JSON."""

from __future__ import annotations

import json  # noqa: F401
from collections import Counter  # noqa: F401
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass  # noqa: F401

from crawler.models import BrokenLink, PageResult, Redirect


@dataclass(frozen=True, slots=True)
class CrawlReport:
    """Everything a crawl found.

    Attributes:
        start_url: Normalized start URL.
        pages: Every fetched URL's result, sorted by URL.
        broken: Failing URLs with the pages that link to them, sorted by URL.
        redirects: Redirects in the order they were seen.
        blocked: URLs skipped because ``robots.txt`` disallowed them, sorted.
        external: Off-site links that were found but not fetched, sorted.
        depth_counts: Number of fetched pages at each depth.
        truncated: Whether ``max_pages`` stopped the crawl from scheduling more URLs.
    """

    start_url: str
    pages: tuple[PageResult, ...]
    broken: tuple[BrokenLink, ...]
    redirects: tuple[Redirect, ...]
    blocked: tuple[str, ...]
    external: tuple[str, ...]
    depth_counts: Mapping[int, int]
    truncated: bool

    @property
    def max_depth_reached(self) -> int:
        """The deepest level at which a page was fetched (``0`` for an empty crawl)."""
        # TODO: max() of the depth_counts keys, default 0.
        raise NotImplementedError

    def to_dict(self) -> dict[str, object]:
        """Convert the report to JSON-ready built-in types.

        Returns:
            A dictionary with ``summary``, ``broken``, ``redirects``, ``blocked``, ``external``, and ``pages`` keys.
        """
        # TODO: See test_report_round_trips_through_json for the exact shape.
        raise NotImplementedError

    def to_json(self, indent: int | None = 2) -> str:
        """Serialize the report.

        Args:
            indent: JSON indentation; ``None`` for a single line.

        Returns:
            The JSON document.
        """
        # TODO: json.dumps(self.to_dict(), indent=indent).
        raise NotImplementedError


def build_report(
    start_url: str,
    results: Iterable[PageResult],
    referrers: Mapping[str, Iterable[str]],
    redirects: Iterable[Redirect] = (),
    blocked: Iterable[str] = (),
    external: Iterable[str] = (),
    *,
    truncated: bool = False,
) -> CrawlReport:
    """Assemble a :class:`CrawlReport`.

    A result is broken when it has no status (every attempt raised) or its status is 400 or higher.

    Args:
        start_url: Normalized start URL.
        results: One result per fetched URL.
        referrers: URL to the pages that link to it.
        redirects: Redirects seen.
        blocked: URLs skipped by ``robots.txt``.
        external: Off-site links found.
        truncated: Whether the page budget ran out.

    Returns:
        The report.
    """
    # TODO: Sort pages by URL; a page is broken when not page.ok; attach sorted referrers.
    #   De-duplicate and sort blocked/external; count pages per depth with collections.Counter.
    raise NotImplementedError
