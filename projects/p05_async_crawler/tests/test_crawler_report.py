"""Milestone 6: the JSON report and the command-line entry point."""

import json

import pytest
from crawler.cli import main
from crawler.fetcher import FakeFetcher, html_response, redirect_response
from crawler.models import CrawlConfig, PageResult, Redirect, Response
from crawler.report import build_report

BASE = "https://docs.example.com"


def sample_report():
    results = [
        PageResult(f"{BASE}/", 0, 200),
        PageResult(f"{BASE}/b", 1, 404),
        PageResult(f"{BASE}/a", 1, None, attempts=3, error="timeout"),
        PageResult(f"{BASE}/old", 1, 301),
    ]
    referrers = {f"{BASE}/b": {f"{BASE}/", f"{BASE}/a"}, f"{BASE}/a": {f"{BASE}/"}}
    redirects = [Redirect(f"{BASE}/old", f"{BASE}/", 301)]
    return build_report(f"{BASE}/", results, referrers, redirects, ["z", "y", "z"], ["https://x.org/"], truncated=True)


def test_broken_links_are_sorted_with_sorted_referrers() -> None:
    report = sample_report()
    assert [b.url for b in report.broken] == [f"{BASE}/a", f"{BASE}/b"], "broken links are sorted by URL"
    assert report.broken[1].referrers == (f"{BASE}/", f"{BASE}/a"), "referrers are sorted for stable output"
    assert report.broken[0].error == "timeout" and report.broken[0].status is None, "network failures keep the error"


def test_redirects_are_not_broken() -> None:
    assert f"{BASE}/old" not in {b.url for b in sample_report().broken}, "a 301 is a redirect, not a broken link"


def test_depth_counts_and_deduplicated_lists() -> None:
    report = sample_report()
    assert dict(report.depth_counts) == {0: 1, 1: 3}, "depth_counts counts fetched pages per depth"
    assert report.blocked == ("y", "z"), "blocked URLs are de-duplicated and sorted"
    assert report.max_depth_reached == 1, "the deepest fetched page is at depth 1"


def test_report_round_trips_through_json() -> None:
    data = json.loads(sample_report().to_json())
    assert data["summary"] == {
        "pages_fetched": 4,
        "broken": 2,
        "redirects": 1,
        "blocked": 2,
        "external": 1,
        "max_depth_reached": 1,
        "depth_counts": {"0": 1, "1": 3},
        "truncated": True,
    }, f"unexpected summary: {data['summary']}"
    assert data["broken"][1] == {
        "url": f"{BASE}/b",
        "status": 404,
        "error": None,
        "referrers": [f"{BASE}/", f"{BASE}/a"],
    }, "each broken link serializes its url, status, error, and referrers"
    assert data["redirects"] == [{"source": f"{BASE}/old", "target": f"{BASE}/", "status": 301}], "redirects serialize"


def test_empty_report() -> None:
    report = build_report(f"{BASE}/", [], {})
    assert report.broken == () and report.max_depth_reached == 0, "an empty crawl has no broken links and depth 0"


@pytest.mark.parametrize(
    "kwargs", [{"max_depth": -1}, {"max_pages": 0}, {"concurrency": 0}, {"retries": -1}, {"per_host_interval": -1}]
)
def test_config_rejects_impossible_settings(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        CrawlConfig(**kwargs)


def test_response_helpers() -> None:
    assert Response(200, {"content-TYPE": "text/HTML"}).is_html, "header lookup is case-insensitive"
    assert redirect_response("/x").is_redirect, "a 301 with Location is a redirect"
    assert not Response(301, {}).is_redirect, "a 3xx without Location cannot be followed"
    assert Response(200).header("x-missing", "dflt") == "dflt", "missing headers return the default"


def test_cli_prints_json_and_exits_1_when_links_are_broken(capsys: pytest.CaptureFixture[str]) -> None:
    fetcher = FakeFetcher({f"{BASE}/": html_response('<a href="/gone">x</a>')})
    code = main([f"{BASE}/", "--interval", "0", "--ignore-robots"], fetcher=fetcher)
    data = json.loads(capsys.readouterr().out)
    assert code == 1, "exit status 1 signals broken links (useful in CI)"
    assert data["broken"][0]["url"] == f"{BASE}/gone", "the report lists the broken link"


def test_cli_exits_0_for_a_healthy_site_and_2_for_a_bad_url(capsys: pytest.CaptureFixture[str]) -> None:
    fetcher = FakeFetcher({f"{BASE}/": html_response("<p>fine</p>")})
    assert main([f"{BASE}/", "--interval", "0"], fetcher=fetcher) == 0, "no broken links means exit 0"
    assert main(["not a url"], fetcher=fetcher) == 2, "an invalid start URL exits 2"
    assert "error:" in capsys.readouterr().err, "the error goes to stderr"
