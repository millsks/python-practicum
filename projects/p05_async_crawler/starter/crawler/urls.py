"""URL normalization and same-site filtering built on :mod:`urllib.parse`."""

from __future__ import annotations

from urllib.parse import urljoin, urlsplit, urlunsplit  # noqa: F401

DEFAULT_PORTS = {"http": 80, "https": 443}
CRAWLABLE_SCHEMES = frozenset(DEFAULT_PORTS)


def remove_dot_segments(path: str) -> str:
    """Resolve ``.`` and ``..`` segments the way RFC 3986 section 5.2.4 describes.

    Args:
        path: A URL path such as ``/a/b/../c/./d``.

    Returns:
        The path without dot segments, keeping a trailing slash when the input implies one.
    """
    # TODO: Walk the '/'-separated segments: skip '.', pop the output on '..' (never above the root),
    #   keep everything else. Keep a trailing slash when the last segment was '.' or '..'.
    raise NotImplementedError


def normalize_url(url: str, base: str | None = None) -> str | None:
    """Turn a raw link into a canonical absolute URL, or reject it.

    The scheme and host are lowercased, default ports and fragments are dropped, dot segments are
    resolved, and an empty path becomes ``/``. The query string is kept as-is.

    Args:
        url: The link as written, possibly relative.
        base: URL of the page the link appeared on, used to resolve relative links.

    Returns:
        The normalized URL, or ``None`` for empty links and non-HTTP schemes such as ``mailto:``.
    """
    # TODO: 1. strip; reject '' and pure '#fragment' links (return None).
    #   2. urljoin(base, url) when base is given.
    #   3. urlsplit; parts.port raises ValueError for bad ports -> return None.
    #   4. only http/https with a hostname are crawlable.
    #   5. lowercase scheme + host, drop default ports, remove_dot_segments(path), drop the fragment.
    raise NotImplementedError


def host_of(url: str) -> str:
    """Return the lowercase host name of ``url``.

    Args:
        url: An absolute URL.

    Returns:
        The host name, or an empty string when there is none.
    """
    # TODO: urlsplit(url).hostname may be None.
    raise NotImplementedError


def same_site(url: str, root: str, *, allow_subdomains: bool = False) -> bool:
    """Decide whether ``url`` belongs to the site rooted at ``root``.

    Args:
        url: Candidate absolute URL.
        root: The crawl's start URL.
        allow_subdomains: Also accept hosts that end with ``.<root host>``.

    Returns:
        ``True`` when the hosts match (or ``url`` is on a subdomain and that is allowed).
    """
    # TODO: Compare hosts exactly; with allow_subdomains also accept host.endswith('.' + root_host).
    raise NotImplementedError


def robots_url(url: str) -> str:
    """Return the ``robots.txt`` location for the site that serves ``url``.

    Args:
        url: Any absolute URL on the site.

    Returns:
        ``scheme://host[:port]/robots.txt``.
    """
    # TODO: Keep scheme and netloc, use path '/robots.txt', no query or fragment.
    raise NotImplementedError
