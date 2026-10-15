"""Milestone 1: link extraction with html.parser."""

from crawler.links import LinkExtractor, extract_links

PAGE = "https://docs.example.com/guide/"


def test_extracts_anchor_links_in_order_without_duplicates() -> None:
    html = '<p><a href="a.html">A</a> <a href="/b">B</a> <a href="a.html#x">A again</a></p>'
    assert extract_links(html, PAGE) == ["https://docs.example.com/guide/a.html", "https://docs.example.com/b"], (
        "links should be absolute, de-duplicated after normalization, and in first-seen order"
    )


def test_ignores_non_http_links_and_anchors_without_href() -> None:
    html = '<a name="top"></a><a href="mailto:x@y.z">mail</a><a href="javascript:go()">js</a><a href="#s">s</a>'
    assert extract_links(html, PAGE) == [], "anchors without crawlable hrefs produce no links"


def test_respects_base_href() -> None:
    html = '<head><base href="https://docs.example.com/v2/"></head><a href="start.html">s</a>'
    assert extract_links(html, PAGE) == ["https://docs.example.com/v2/start.html"], "relative links use <base href>"


def test_skips_nofollow_and_reads_area_tags() -> None:
    html = '<a rel="nofollow" href="/ads">ad</a><map><area href="/map-target"></map>'
    assert extract_links(html, PAGE) == ["https://docs.example.com/map-target"], (
        "rel=nofollow links are skipped and <area href> counts as a link"
    )


def test_entities_in_href_are_decoded() -> None:
    html = '<a href="/search?q=a&amp;page=2">next</a>'
    assert extract_links(html, PAGE) == ["https://docs.example.com/search?q=a&page=2"], "&amp; decodes to &"


def test_extractor_tolerates_broken_html() -> None:
    parser = LinkExtractor()
    parser.feed('<div><a href="/one">one<p><a href=/two>two</div></span>')
    parser.close()
    assert parser.hrefs == ["/one", "/two"], "html.parser is forgiving; unclosed tags must not lose links"
