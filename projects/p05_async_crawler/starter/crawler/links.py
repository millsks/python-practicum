"""Extract links from HTML with the standard library's :mod:`html.parser`."""

from __future__ import annotations

from html.parser import HTMLParser

from crawler.urls import normalize_url  # noqa: F401

LINK_TAGS = frozenset({"a", "area"})


class LinkExtractor(HTMLParser):
    """Collect ``href`` values from ``<a>`` and ``<area>`` tags, honoring ``<base href>``.

    Attributes:
        hrefs: Raw ``href`` values in document order.
        base_href: The first ``<base href>`` seen, if any.
    """

    def __init__(self) -> None:
        """Create an extractor with no links collected yet."""
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.base_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record links and the document base as tags are parsed.

        Args:
            tag: Lowercase tag name.
            attrs: Attribute name/value pairs.
        """
        # TODO: dict(attrs) gives {'href': ...}. Remember the first <base href>.
        #   Collect href from LINK_TAGS unless rel contains 'nofollow'.
        raise NotImplementedError


def extract_links(html: str, page_url: str) -> list[str]:
    """Return the unique, normalized links on a page in first-seen order.

    Args:
        html: The page body.
        page_url: URL the page was fetched from; relative links resolve against it (or ``<base href>``).

    Returns:
        Absolute HTTP(S) URLs without fragments. ``mailto:``, ``javascript:`` and ``rel="nofollow"`` links are
        dropped.
    """
    # TODO: Feed the HTML to a LinkExtractor, resolve <base href> against page_url, then normalize every href.
    #   Drop None results and duplicates while keeping first-seen order (a dict works as an ordered set).
    raise NotImplementedError
