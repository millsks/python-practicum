"""URL normalization and same-site filtering built on :mod:`urllib.parse`."""

from __future__ import annotations

from urllib.parse import urljoin, urlsplit, urlunsplit

DEFAULT_PORTS = {"http": 80, "https": 443}
CRAWLABLE_SCHEMES = frozenset(DEFAULT_PORTS)


def remove_dot_segments(path: str) -> str:
    """Resolve ``.`` and ``..`` segments the way RFC 3986 section 5.2.4 describes.

    Args:
        path: A URL path such as ``/a/b/../c/./d``.

    Returns:
        The path without dot segments, keeping a trailing slash when the input implies one.
    """
    if not path:
        return "/"
    output: list[str] = []
    segments = path.split("/")
    for segment in segments[1:] if path.startswith("/") else segments:
        if segment == "..":
            if output:
                output.pop()
        elif segment != ".":
            output.append(segment)
    trailing = segments[-1] in {".", ".."}
    result = "/" + "/".join(output)
    if trailing and not result.endswith("/"):
        result += "/"
    return result


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
    raw = url.strip()
    if not raw or raw.startswith("#"):
        return None
    absolute = urljoin(base, raw) if base else raw
    try:
        parts = urlsplit(absolute)
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    if scheme not in CRAWLABLE_SCHEMES or not parts.hostname:
        return None
    host = parts.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    netloc = host if port is None or port == DEFAULT_PORTS[scheme] else f"{host}:{port}"
    return urlunsplit((scheme, netloc, remove_dot_segments(parts.path), parts.query, ""))


def host_of(url: str) -> str:
    """Return the lowercase host name of ``url``.

    Args:
        url: An absolute URL.

    Returns:
        The host name, or an empty string when there is none.
    """
    return (urlsplit(url).hostname or "").lower()


def same_site(url: str, root: str, *, allow_subdomains: bool = False) -> bool:
    """Decide whether ``url`` belongs to the site rooted at ``root``.

    Args:
        url: Candidate absolute URL.
        root: The crawl's start URL.
        allow_subdomains: Also accept hosts that end with ``.<root host>``.

    Returns:
        ``True`` when the hosts match (or ``url`` is on a subdomain and that is allowed).
    """
    host, root_host = host_of(url), host_of(root)
    if not host or not root_host:
        return False
    return host == root_host or (allow_subdomains and host.endswith("." + root_host))


def robots_url(url: str) -> str:
    """Return the ``robots.txt`` location for the site that serves ``url``.

    Args:
        url: Any absolute URL on the site.

    Returns:
        ``scheme://host[:port]/robots.txt``.
    """
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
