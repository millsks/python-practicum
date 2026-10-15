"""Milestone 1: URL normalization and same-site filtering."""

import pytest
from crawler.urls import host_of, normalize_url, remove_dot_segments, robots_url, same_site

PAGE = "https://docs.example.com/guide/intro.html"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("install.html", "https://docs.example.com/guide/install.html"),
        ("../api/", "https://docs.example.com/api/"),
        ("/faq", "https://docs.example.com/faq"),
        ("//cdn.example.com/x.js", "https://cdn.example.com/x.js"),
        ("?page=2", "https://docs.example.com/guide/intro.html?page=2"),
    ],
)
def test_relative_links_resolve_against_the_page(raw: str, expected: str) -> None:
    assert normalize_url(raw, PAGE) == expected, f"{raw!r} on {PAGE} should resolve to {expected}"


def test_scheme_and_host_are_lowercased() -> None:
    assert normalize_url("HTTPS://Docs.Example.COM/Path") == "https://docs.example.com/Path", (
        "scheme and host are case-insensitive and should be lowercased; the path is case-sensitive and kept"
    )


def test_default_ports_are_dropped_but_others_kept() -> None:
    assert normalize_url("http://example.com:80/a") == "http://example.com/a", "port 80 is the http default"
    assert normalize_url("https://example.com:443/a") == "https://example.com/a", "port 443 is the https default"
    assert normalize_url("http://example.com:8080/a") == "http://example.com:8080/a", "non-default ports stay"


def test_fragment_is_removed_and_empty_path_becomes_slash() -> None:
    assert normalize_url("https://example.com#top") == "https://example.com/", "fragments never reach the server"
    assert normalize_url("https://example.com/a?x=1#s") == "https://example.com/a?x=1", (
        "query is kept, fragment dropped"
    )


@pytest.mark.parametrize(
    "raw", ["mailto:help@example.com", "javascript:void(0)", "tel:+15551234", "#section", "", "  "]
)
def test_non_crawlable_links_are_rejected(raw: str) -> None:
    assert normalize_url(raw, PAGE) is None, f"{raw!r} is not an HTTP(S) page and should normalize to None"


def test_invalid_port_is_rejected() -> None:
    assert normalize_url("http://example.com:99999/") is None, "an out-of-range port should be rejected, not raise"


@pytest.mark.parametrize(
    ("path", "expected"),
    [("/a/b/../c/./d", "/a/c/d"), ("/a/b/", "/a/b/"), ("/a/b/..", "/a/"), ("/../../x", "/x"), ("", "/")],
)
def test_remove_dot_segments(path: str, expected: str) -> None:
    assert remove_dot_segments(path) == expected, f"remove_dot_segments({path!r}) should be {expected!r}"


def test_same_site_matches_hosts_exactly_by_default() -> None:
    root = "https://example.com/"
    assert same_site("https://example.com/docs", root), "same host is the same site"
    assert not same_site("https://docs.example.com/", root), "subdomains are off-site unless allowed"
    assert not same_site("https://example.com.evil.org/", root), "a suffix trick must not count as the same site"
    assert same_site("https://docs.example.com/", root, allow_subdomains=True), "allowed subdomain should match"
    assert not same_site("https://notexample.com/", root, allow_subdomains=True), "only real subdomains match"


def test_host_and_robots_url() -> None:
    assert host_of("https://Docs.Example.com:8443/x") == "docs.example.com", "host_of returns the lowercase hostname"
    assert robots_url("https://example.com:8443/a/b?c=1") == "https://example.com:8443/robots.txt", (
        "robots.txt lives at the root of the same scheme, host, and port"
    )
