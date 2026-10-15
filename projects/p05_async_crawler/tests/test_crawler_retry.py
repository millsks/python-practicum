"""Milestone 3: retries with exponential backoff and jitter."""

import asyncio
import random

import pytest
from crawler.fetcher import FakeFetcher, FetchError, html_response
from crawler.models import Response
from crawler.retry import backoff_ceiling, backoff_delay, fetch_with_retries

URL = "https://example.com/page"


class RecordingSleep:
    """An async sleep that records delays instead of waiting."""

    def __init__(self) -> None:
        """Start with no recorded delays."""
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        """Record ``delay`` and yield once to the event loop."""
        self.delays.append(delay)
        await asyncio.sleep(0)


def run_fetch(fetcher: FakeFetcher, retries: int = 3, seed: int = 1) -> tuple[object, RecordingSleep]:
    sleep = RecordingSleep()
    outcome = asyncio.run(
        fetch_with_retries(fetcher, URL, retries=retries, base=0.5, cap=4.0, rng=random.Random(seed), sleep=sleep)
    )
    return outcome, sleep


def test_backoff_ceiling_doubles_then_caps() -> None:
    ceilings = [backoff_ceiling(n, 0.5, 4.0) for n in range(6)]
    assert ceilings == [0.5, 1.0, 2.0, 4.0, 4.0, 4.0], f"ceilings should double from base and stop at cap: {ceilings}"


def test_backoff_delay_has_full_jitter_within_the_ceiling() -> None:
    rng = random.Random(42)
    delays = [backoff_delay(3, 0.5, 4.0, rng) for _ in range(200)]
    assert all(0.0 <= d <= 4.0 for d in delays), "every jittered delay must lie in [0, ceiling]"
    assert len({round(d, 6) for d in delays}) > 150, "jitter should spread delays out, not repeat one value"


def test_backoff_delay_is_reproducible_with_a_seeded_rng() -> None:
    first = [backoff_delay(n, 0.1, 2.0, random.Random(7)) for n in range(4)]
    second = [backoff_delay(n, 0.1, 2.0, random.Random(7)) for n in range(4)]
    assert first == second, "an injected, seeded Random must make delays reproducible"


def test_success_on_first_try_does_not_sleep() -> None:
    outcome, sleep = run_fetch(FakeFetcher({URL: html_response("ok")}))
    assert outcome.response.status == 200 and outcome.attempts == 1, "a 200 needs exactly one attempt"
    assert sleep.delays == [], "no backoff sleep when the first attempt succeeds"


def test_transient_errors_are_retried_until_success() -> None:
    fetcher = FakeFetcher({URL: [FetchError("reset"), Response(503), html_response("ok")]})
    outcome, sleep = run_fetch(fetcher)
    assert outcome.response.status == 200, "the third attempt succeeds and should be returned"
    assert outcome.attempts == 3 and fetcher.count(URL) == 3, "two failures then one success is three attempts"
    assert len(sleep.delays) == 2, "there is one backoff sleep between each pair of attempts"
    assert sleep.delays[0] <= 0.5 and sleep.delays[1] <= 1.0, f"delays must respect the ceilings: {sleep.delays}"
    assert list(outcome.delays) == sleep.delays, "the outcome should report the delays it slept"


def test_gives_up_after_retries_and_reports_the_error() -> None:
    outcome, sleep = run_fetch(FakeFetcher({URL: FetchError("dns failure")}), retries=2)
    assert outcome.response is None, "no response when every attempt raised"
    assert outcome.attempts == 3, "retries=2 means 1 + 2 attempts"
    assert outcome.error == "dns failure", "the last error message should be reported"
    assert len(sleep.delays) == 2, "two retries mean two sleeps"


def test_final_status_is_returned_when_5xx_never_recovers() -> None:
    outcome, _ = run_fetch(FakeFetcher({URL: Response(500)}), retries=1)
    assert outcome.response.status == 500 and outcome.attempts == 2, "a persistent 500 is returned after retrying"


@pytest.mark.parametrize("status", [404, 403, 410, 301])
def test_non_retryable_statuses_are_final(status: int) -> None:
    fetcher = FakeFetcher({URL: Response(status, {"Location": "/x"})})
    outcome, sleep = run_fetch(fetcher)
    assert outcome.attempts == 1 and sleep.delays == [], f"status {status} is final and must not be retried"
