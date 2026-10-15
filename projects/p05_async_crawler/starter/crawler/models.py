"""Plain data types shared by every part of the crawler."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class Response:
    """What a fetcher returns for one URL.

    Attributes:
        status: HTTP status code.
        headers: Response headers. Lookups through :meth:`header` ignore case.
        body: Decoded response body.
    """

    status: int
    headers: Mapping[str, str] = field(default_factory=dict)
    body: str = ""

    def header(self, name: str, default: str = "") -> str:
        """Return a header value, matching the name case-insensitively.

        Args:
            name: Header name such as ``"Content-Type"``.
            default: Value returned when the header is absent.

        Returns:
            The header value or ``default``.
        """
        wanted = name.lower()
        for key, value in self.headers.items():
            if key.lower() == wanted:
                return value
        return default

    @property
    def is_html(self) -> bool:
        """Whether the body is HTML according to ``Content-Type``."""
        return "html" in self.header("content-type").lower()

    @property
    def is_redirect(self) -> bool:
        """Whether this is a redirect that carries a ``Location`` header."""
        return self.status in REDIRECT_STATUSES and bool(self.header("location"))


@dataclass(frozen=True, slots=True)
class CrawlConfig:
    """Knobs that control a crawl.

    Attributes:
        max_depth: Deepest link level to fetch; the start URL is depth 0.
        max_pages: Upper bound on the number of URLs fetched.
        concurrency: Number of worker tasks fetching at the same time.
        per_host_interval: Minimum seconds between two requests to the same host.
        retries: Extra attempts after a transient failure.
        backoff_base: First retry delay ceiling in seconds; doubles every attempt.
        backoff_cap: Largest retry delay ceiling in seconds.
        respect_robots: Whether to fetch and obey ``robots.txt``.
        user_agent: Agent name used for ``robots.txt`` matching.
        allow_subdomains: Treat ``docs.example.com`` as inside ``example.com``.
    """

    max_depth: int = 3
    max_pages: int = 200
    concurrency: int = 4
    per_host_interval: float = 0.0
    retries: int = 2
    backoff_base: float = 0.1
    backoff_cap: float = 2.0
    respect_robots: bool = True
    user_agent: str = "practicum-crawler"
    allow_subdomains: bool = False

    def __post_init__(self) -> None:
        """Reject settings that cannot work.

        Raises:
            ValueError: If a numeric setting is out of range.
        """
        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if self.max_pages < 1:
            raise ValueError("max_pages must be >= 1")
        if self.concurrency < 1:
            raise ValueError("concurrency must be >= 1")
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        if self.per_host_interval < 0 or self.backoff_base < 0 or self.backoff_cap < 0:
            raise ValueError("intervals and backoff delays must be >= 0")


@dataclass(frozen=True, slots=True)
class PageResult:
    """The outcome of fetching one URL.

    Attributes:
        url: Normalized URL that was fetched.
        depth: Link distance from the start URL.
        status: Final HTTP status, or ``None`` when every attempt raised.
        attempts: Number of fetch attempts made.
        error: Description of the last error, if the fetch failed without a status.
        links: Normalized same-site links found on the page.
    """

    url: str
    depth: int
    status: int | None
    attempts: int = 1
    error: str | None = None
    links: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        """Whether the URL resolved to a non-error response."""
        return self.status is not None and self.status < 400


@dataclass(frozen=True, slots=True)
class BrokenLink:
    """A URL that failed, plus the pages that link to it.

    Attributes:
        url: The failing URL.
        status: HTTP status, or ``None`` for network errors.
        error: Error description for network failures.
        referrers: Sorted pages that link to ``url``.
    """

    url: str
    status: int | None
    error: str | None
    referrers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Redirect:
    """A redirect seen during the crawl.

    Attributes:
        source: URL that answered with a redirect.
        target: Normalized ``Location`` it pointed to.
        status: Redirect status code.
    """

    source: str
    target: str
    status: int
