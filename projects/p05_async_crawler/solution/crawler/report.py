"""Turn raw crawl results into a broken-link report that serializes to JSON."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass

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
        return max(self.depth_counts, default=0)

    def to_dict(self) -> dict[str, object]:
        """Convert the report to JSON-ready built-in types.

        Returns:
            A dictionary with ``summary``, ``broken``, ``redirects``, ``blocked``, ``external``, and ``pages`` keys.
        """
        return {
            "start_url": self.start_url,
            "summary": {
                "pages_fetched": len(self.pages),
                "broken": len(self.broken),
                "redirects": len(self.redirects),
                "blocked": len(self.blocked),
                "external": len(self.external),
                "max_depth_reached": self.max_depth_reached,
                "depth_counts": {str(depth): count for depth, count in sorted(self.depth_counts.items())},
                "truncated": self.truncated,
            },
            "broken": [asdict(link) | {"referrers": list(link.referrers)} for link in self.broken],
            "redirects": [asdict(redirect) for redirect in self.redirects],
            "blocked": list(self.blocked),
            "external": list(self.external),
            "pages": [
                {"url": p.url, "depth": p.depth, "status": p.status, "attempts": p.attempts, "error": p.error}
                for p in self.pages
            ],
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Serialize the report.

        Args:
            indent: JSON indentation; ``None`` for a single line.

        Returns:
            The JSON document.
        """
        return json.dumps(self.to_dict(), indent=indent)


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
    pages = tuple(sorted(results, key=lambda r: r.url))
    broken = tuple(
        BrokenLink(page.url, page.status, page.error, tuple(sorted(referrers.get(page.url, ()))))
        for page in pages
        if not page.ok
    )
    return CrawlReport(
        start_url=start_url,
        pages=pages,
        broken=broken,
        redirects=tuple(redirects),
        blocked=tuple(sorted(set(blocked))),
        external=tuple(sorted(set(external))),
        depth_counts=dict(sorted(Counter(page.depth for page in pages).items())),
        truncated=truncated,
    )
