"""Extract links from HTML with the standard library's :mod:`html.parser`."""

from __future__ import annotations

from html.parser import HTMLParser

from crawler.urls import normalize_url

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
        attributes = dict(attrs)
        href = attributes.get("href")
        if href is None:
            return
        if tag == "base" and self.base_href is None:
            self.base_href = href
        elif tag in LINK_TAGS and "nofollow" not in (attributes.get("rel") or "").lower().split():
            self.hrefs.append(href)


def extract_links(html: str, page_url: str) -> list[str]:
    """Return the unique, normalized links on a page in first-seen order.

    Args:
        html: The page body.
        page_url: URL the page was fetched from; relative links resolve against it (or ``<base href>``).

    Returns:
        Absolute HTTP(S) URLs without fragments. ``mailto:``, ``javascript:`` and ``rel="nofollow"`` links are
        dropped.
    """
    parser = LinkExtractor()
    parser.feed(html)
    parser.close()
    base = normalize_url(parser.base_href, page_url) if parser.base_href else page_url
    seen: dict[str, None] = {}
    for href in parser.hrefs:
        url = normalize_url(href, base or page_url)
        if url is not None:
            seen.setdefault(url, None)
    return list(seen)
