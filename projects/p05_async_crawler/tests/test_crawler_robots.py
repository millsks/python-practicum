"""Milestone 2: robots.txt rules."""

from crawler.models import Response
from crawler.robots import RobotsPolicy

ROBOTS = """
User-agent: badbot
Disallow: /

User-agent: *
Disallow: /private/
Crawl-delay: 2
"""


def test_disallowed_paths_are_blocked() -> None:
    policy = RobotsPolicy.from_text(ROBOTS, "practicum-crawler")
    assert not policy.allowed("https://example.com/private/keys"), "/private/ is disallowed for every agent"
    assert policy.allowed("https://example.com/guide/"), "other paths are allowed"


def test_rules_are_per_user_agent() -> None:
    policy = RobotsPolicy.from_text(ROBOTS, "badbot")
    assert not policy.allowed("https://example.com/guide/"), "badbot is disallowed everywhere"


def test_crawl_delay_is_exposed() -> None:
    assert RobotsPolicy.from_text(ROBOTS, "practicum-crawler").crawl_delay() == 2.0, (
        "Crawl-delay should be read (robotparser only accepts whole seconds)"
    )
    assert RobotsPolicy.allow_all("x").crawl_delay() == 0.0, "no rules means no delay"


def test_missing_robots_allows_everything() -> None:
    for response in (Response(404, {}, "nope"), None):
        policy = RobotsPolicy.from_response(response, "practicum-crawler")
        assert policy.allowed("https://example.com/private/x"), f"{response!r} means no rules, so all URLs are allowed"


def test_from_response_parses_a_200_body() -> None:
    policy = RobotsPolicy.from_response(Response(200, {}, ROBOTS), "practicum-crawler")
    assert not policy.allowed("https://example.com/private/"), "a 200 robots.txt body should be parsed"
