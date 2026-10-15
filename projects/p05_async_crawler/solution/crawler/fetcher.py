"""The fetcher seam: a Protocol, an in-memory fake for tests, and a real urllib-based fetcher."""

from __future__ import annotations

import asyncio
import urllib.error
import urllib.request
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Protocol, runtime_checkable

from crawler.models import Response

Outcome = Response | Exception
Script = Outcome | Sequence[Outcome]


class FetchError(Exception):
    """A transient network failure: DNS, connection reset, timeout, and similar."""


@runtime_checkable
class Fetcher(Protocol):
    """Anything that can fetch a URL asynchronously.

    The crawler depends only on this Protocol, so tests inject :class:`FakeFetcher` and production code injects
    :class:`UrllibFetcher` (or an ``httpx``-based fetcher) without the crawler knowing the difference.
    """

    async def fetch(self, url: str) -> Response:
        """Fetch ``url`` without following redirects.

        Args:
            url: Absolute URL.

        Returns:
            The response, including 3xx, 4xx, and 5xx answers.

        Raises:
            FetchError: For transient network failures.
        """
        ...


def html_response(body: str, status: int = 200) -> Response:
    """Build an HTML response, a convenience for tests and examples.

    Args:
        body: HTML text.
        status: Status code.

    Returns:
        A response with ``Content-Type: text/html``.
    """
    return Response(status, {"Content-Type": "text/html; charset=utf-8"}, body)


def redirect_response(location: str, status: int = 301) -> Response:
    """Build a redirect response.

    Args:
        location: Target of the ``Location`` header.
        status: Redirect status code.

    Returns:
        The response.
    """
    return Response(status, {"Location": location}, "")


class FakeFetcher:
    """An in-memory site with configurable latency and failures.

    Each URL maps to a response, an exception instance to raise, or a sequence of those consumed one per call
    (the last entry repeats), which makes "fail twice, then succeed" easy to script. Unknown URLs answer 404.

    Attributes:
        calls: Every URL fetched, in call order.
        in_flight: Requests currently awaiting their latency.
        max_in_flight: Highest ``in_flight`` value observed.
    """

    def __init__(
        self,
        pages: Mapping[str, Script],
        *,
        latency: float | Mapping[str, float] = 0.0,
        sleep: Callable[[float], Awaitable[object]] | None = None,
    ) -> None:
        """Create a fake site.

        Args:
            pages: URL to scripted outcome(s).
            latency: Seconds every request takes, or a per-URL mapping (missing URLs take 0).
            sleep: Async sleep used for latency; defaults to :func:`asyncio.sleep`.
        """
        self._pages = dict(pages)
        self._latency = latency
        self._sleep = sleep or asyncio.sleep
        self._served: dict[str, int] = {}
        self.calls: list[str] = []
        self.in_flight = 0
        self.max_in_flight = 0

    def _delay_for(self, url: str) -> float:
        if isinstance(self._latency, Mapping):
            return float(self._latency.get(url, 0.0))
        return float(self._latency)

    def _next_outcome(self, url: str) -> Outcome:
        script = self._pages.get(url, Response(404, {"Content-Type": "text/plain"}, "not found"))
        if isinstance(script, Response | Exception):
            return script
        index = self._served.get(url, 0)
        self._served[url] = index + 1
        return script[min(index, len(script) - 1)]

    def count(self, url: str) -> int:
        """Return how many times ``url`` was fetched.

        Args:
            url: URL to count.

        Returns:
            Number of calls.
        """
        return self.calls.count(url)

    async def fetch(self, url: str) -> Response:
        """Serve the scripted outcome for ``url`` after its latency.

        Args:
            url: URL to fetch.

        Returns:
            The scripted response.

        Raises:
            Exception: The scripted exception, when one is configured.
        """
        self.calls.append(url)
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            delay = self._delay_for(url)
            if delay > 0:
                await self._sleep(delay)
            else:
                await asyncio.sleep(0)
            outcome = self._next_outcome(url)
        finally:
            self.in_flight -= 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Make urllib surface 3xx answers instead of following them, so the crawler can report redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        """Refuse to follow the redirect; urllib then raises ``HTTPError`` carrying the 3xx status."""
        return None


class UrllibFetcher:
    """A real fetcher built on blocking :mod:`urllib`, run in a worker thread with :func:`asyncio.to_thread`.

    It exists to show how blocking libraries plug into asyncio; the tests never use it (they never touch the
    network). For heavy production crawling, an async HTTP client such as ``httpx`` would avoid one thread per
    in-flight request.
    """

    def __init__(self, *, timeout: float = 10.0, user_agent: str = "practicum-crawler", max_bytes: int = 2_000_000):
        """Create a fetcher.

        Args:
            timeout: Socket timeout in seconds.
            user_agent: ``User-Agent`` header value.
            max_bytes: Largest body read; longer bodies are truncated.
        """
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_bytes = max_bytes
        self._opener = urllib.request.build_opener(_NoRedirect)

    def _fetch_sync(self, url: str) -> Response:
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with self._opener.open(request, timeout=self.timeout) as reply:
                charset = reply.headers.get_content_charset() or "utf-8"
                body = reply.read(self.max_bytes).decode(charset, errors="replace")
                return Response(reply.status, dict(reply.headers.items()), body)
        except urllib.error.HTTPError as exc:
            body = exc.read(self.max_bytes).decode("utf-8", errors="replace") if exc.fp else ""
            return Response(exc.code, dict(exc.headers.items()), body)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise FetchError(f"{url}: {exc}") from exc

    async def fetch(self, url: str) -> Response:
        """Fetch ``url`` in a worker thread so the event loop stays responsive.

        Args:
            url: Absolute URL.

        Returns:
            The response, including 3xx and error statuses.

        Raises:
            FetchError: For network failures.
        """
        return await asyncio.to_thread(self._fetch_sync, url)
