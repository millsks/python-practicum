import io
import json
import logging
import random
import urllib.error
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from invoicer import cli, config, invoices, rates

LINES = [{"qty": 2, "cents": 500}]


@pytest.fixture(autouse=True)
def controlled_world(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Pin everything the code reads implicitly, so no test depends on the machine."""

    class FrozenDate(date):
        @classmethod
        def today(cls) -> "FrozenDate":
            return cls(2026, 3, 1)

    for name in ("INVOICER_CURRENCY", "INVOICER_TAX"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("INVOICER_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(invoices, "date", FrozenDate)
    monkeypatch.setattr(invoices, "HISTORY", [])
    monkeypatch.setattr(invoices.random, "randint", lambda low, high: 1234)


@pytest.fixture
def no_rate_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(currency: str) -> float:
        raise AssertionError("USD invoices must not look up a rate")

    monkeypatch.setattr(invoices, "fetch_rate", refuse)


def test_config_defaults() -> None:
    assert config.load_config() == {"currency": "USD", "tax": 0.2}


def test_config_reads_and_normalizes_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INVOICER_CURRENCY", "eur")
    monkeypatch.setenv("INVOICER_TAX", "0.1")
    assert config.load_config() == {"currency": "EUR", "tax": 0.1}


@pytest.mark.parametrize("value", [pytest.param("lots", id="not-a-number"), "1", "1.5", "-0.1"])
def test_config_rejects_a_bad_tax(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("INVOICER_TAX", value)
    with pytest.raises(ValueError, match="INVOICER_TAX"):
        config.load_config()


def test_config_allows_zero_tax(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INVOICER_TAX", "0")
    assert config.load_config()["tax"] == 0


def test_fetch_rate_reads_the_response(monkeypatch: pytest.MonkeyPatch) -> None:
    urls: list[str] = []

    def fake_urlopen(url: str, timeout: float) -> io.BytesIO:
        urls.append(url)
        return io.BytesIO(json.dumps({"rate": 0.5}).encode())

    monkeypatch.setattr(rates.urllib.request, "urlopen", fake_urlopen)
    assert rates.fetch_rate("EUR") == 0.5
    assert urls == ["https://rates.example.test/latest?symbol=EUR"]


def _failing_urlopen(attempts: list[int]) -> Any:
    def fake(url: str, timeout: float) -> io.BytesIO:
        attempts.append(1)
        raise urllib.error.URLError("down")

    return fake


def test_fetch_rate_backs_off_then_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts: list[int] = []
    sleeps: list[float] = []
    monkeypatch.setattr(rates.urllib.request, "urlopen", _failing_urlopen(attempts))
    monkeypatch.setattr(rates.time, "sleep", sleeps.append)
    with pytest.raises(rates.RateError, match="EUR"):
        rates.fetch_rate("EUR")
    assert len(attempts) == 3
    assert sleeps == [1, 2]


def test_fetch_rate_recovers_after_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter([urllib.error.URLError("down"), io.BytesIO(b'{"rate": 2}')])

    def fake(url: str, timeout: float) -> io.BytesIO:
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(rates.urllib.request, "urlopen", fake)
    monkeypatch.setattr(rates.time, "sleep", lambda seconds: None)
    assert rates.fetch_rate("EUR") == 2


@pytest.mark.usefixtures("no_rate_lookup")
def test_build_invoice_in_usd() -> None:
    assert invoices.build_invoice("Ada", LINES) == {
        "number": "INV-20260301-1234",
        "customer": "Ada",
        "currency": "USD",
        "net": 1000,
        "tax": 200,
        "total": 1200,
        "issued": "2026-03-01",
        "due": "2026-03-31",
    }


def test_build_invoice_converts_currency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INVOICER_CURRENCY", "EUR")
    monkeypatch.setattr(invoices, "fetch_rate", lambda currency: 0.5 if currency == "EUR" else 0.0)
    invoice = invoices.build_invoice("Ada", LINES)
    assert (invoice["net"], invoice["tax"], invoice["total"]) == (500, 100, 600)


def test_build_invoice_needs_lines() -> None:
    with pytest.raises(ValueError, match="at least one line"):
        invoices.build_invoice("Ada", [])


def test_build_invoice_records_history() -> None:
    invoices.build_invoice("Ada", LINES)
    assert invoices.HISTORY == ["INV-20260301-1234"]


def test_number_is_random_within_range(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, int]] = []

    def fake(low: int, high: int) -> int:
        calls.append((low, high))
        return 7777

    monkeypatch.setattr(random, "randint", fake)
    assert invoices.build_invoice("Ada", LINES)["number"].endswith("-7777")
    assert calls == [(1000, 9999)]


@pytest.mark.parametrize(
    ("cents", "warned"),
    [pytest.param(833_333, False, id="just-below"), pytest.param(833_334, True, id="above")],
)
def test_large_invoice_warning(caplog: pytest.LogCaptureFixture, cents: int, warned: bool) -> None:
    invoices.build_invoice("Ada", [{"qty": 1, "cents": cents}])
    assert any("large invoice" in r.getMessage() and r.levelno == logging.WARNING for r in caplog.records) is warned


@pytest.mark.parametrize(
    ("due", "overdue"),
    [
        pytest.param("2026-02-28", True, id="yesterday"),
        pytest.param("2026-03-01", False, id="due-today"),
        pytest.param("2026-03-02", False, id="tomorrow"),
    ],
)
def test_is_overdue(due: str, overdue: bool) -> None:
    assert invoices.is_overdue({"due": due}) is overdue


def test_save_invoice_writes_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = invoices.save_invoice({"number": "N1", "total": 5})
    assert path == tmp_path / "out" / "N1.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {"number": "N1", "total": 5}
    assert capsys.readouterr().out == f"saved {path}\n"


def test_save_invoice_defaults_to_invoices_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("INVOICER_DIR")
    monkeypatch.chdir(tmp_path)
    assert invoices.save_invoice({"number": "N1"}) == Path("invoices") / "N1.json"


def test_save_invoice_warns_on_overwrite(caplog: pytest.LogCaptureFixture) -> None:
    invoices.save_invoice({"number": "N1"})
    assert caplog.records == []
    invoices.save_invoice({"number": "N1"})
    assert ["WARNING"] == [r.levelname for r in caplog.records]


def test_parse_line() -> None:
    assert cli.parse_line("pens,2,150\n") == {"description": "pens", "qty": 2, "cents": 150}


def _stdin(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr(cli.sys, "stdin", io.StringIO(text))


def test_main_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    _stdin(monkeypatch, "pens,2,500\n\n")
    assert cli.main(["Ada"]) == 0
    out = capsys.readouterr().out
    assert out.endswith("INV-20260301-1234 total 1200 USD\n")
    assert (tmp_path / "out" / "INV-20260301-1234.json").exists()


def test_main_reads_sys_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    _stdin(monkeypatch, "pens,2,500\n")
    monkeypatch.setattr(cli.sys, "argv", ["invoicer", "Ada"])
    assert cli.main() == 0


def test_main_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage" in captured.err


@pytest.mark.parametrize("text", [pytest.param("nonsense\n", id="bad-line"), pytest.param("", id="no-lines")])
def test_main_input_errors(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], text: str) -> None:
    _stdin(monkeypatch, text)
    assert cli.main(["Ada"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: ")
