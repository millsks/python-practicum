"""Grade the learner's test suite: it must pass on the real code and catch every planted bug."""

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

LEARNER = Path(os.environ["PRACTICUM_SRC"])
PRISTINE = Path(__file__).resolve().parents[1] / "starter" / "invoicer"
MIN_COVERAGE = "90"
MAX_SECONDS = 20.0

GUARD_PLUGIN = """
import socket

class NetworkBlocked(RuntimeError):
    pass

def _refuse(*args, **kwargs):
    raise NetworkBlocked("a test tried to open a real network connection")

socket.socket.connect = _refuse
socket.socket.connect_ex = _refuse
socket.create_connection = _refuse
socket.getaddrinfo = _refuse
"""
REVERSE_PLUGIN = """
def pytest_collection_modifyitems(items):
    items.reverse()
"""
OTHER_CLOCK = """from datetime import timedelta
from datetime import date as _real_date


class date(_real_date):
    @classmethod
    def today(cls):
        return cls(2031, 7, 15)
"""


@dataclass(frozen=True)
class Mutant:
    """One planted bug: replace ``old`` with ``new`` in a module."""

    id: str
    module: str
    old: str
    new: str
    hint: str


MUTANTS = [
    Mutant("default-currency", "config", '"INVOICER_CURRENCY", "USD"', '"INVOICER_CURRENCY", "EUR"', "the default currency"),
    Mutant("currency-case", "config", '"USD").upper()', '"USD")', "lower-case currency codes being upper-cased"),
    Mutant("default-tax", "config", '"INVOICER_TAX", "0.2"', '"INVOICER_TAX", "0.25"', "the default tax rate"),
    Mutant("tax-upper-bound", "config", "0 <= tax < 1", "0 <= tax <= 1", "a tax rate of exactly 1 being rejected"),
    Mutant("tax-lower-bound", "config", "0 <= tax < 1", "tax < 1", "a negative tax rate being rejected"),
    Mutant("retry-count", "rates", "retries: int = 3", "retries: int = 2", "the number of attempts"),
    Mutant("backoff", "rates", "time.sleep(2**attempt)", "time.sleep(1)", "the backoff delays growing"),
    Mutant("gives-up-silently", "rates", 'raise RateError(f"could not fetch {currency}") from None', "return 0.0", "RateError after the last attempt"),
    Mutant("wrong-rate-value", "rates", '["rate"])', '["rate"] * 2)', "the rate value returned"),
    Mutant("empty-lines", "invoices", 'raise ValueError("an invoice needs at least one line")', "pass", "an invoice with no lines"),
    Mutant("qty-ignored", "invoices", 'line["qty"] * line["cents"]', 'line["cents"]', "quantities being multiplied"),
    Mutant("usd-lookup", "invoices", '1.0 if currency == "USD" else fetch_rate(currency)', "fetch_rate(currency)", "USD invoices not looking up a rate"),
    Mutant("total-without-tax", "invoices", "round((net + tax) * rate)", "round(net * rate)", "the total including tax"),
    Mutant("tax-not-converted", "invoices", '"tax": round(tax * rate)', '"tax": tax', "tax being converted"),
    Mutant("due-date", "invoices", "timedelta(days=30)", "timedelta(days=31)", "the 30-day due date"),
    Mutant("number-range", "invoices", "random.randint(1000, 9999)", "random.randint(0, 9)", "the range of the invoice number"),
    Mutant("no-large-warning", "invoices", 'logger.warning("large invoice %s", invoice["number"])', "pass", "the large invoice warning"),
    Mutant("large-threshold", "invoices", "> 1_000_000", "> 2_000_000", "the large invoice threshold"),
    Mutant("no-history", "invoices", 'HISTORY.append(str(invoice["number"]))', "pass", "invoices being added to HISTORY"),
    Mutant("overdue-boundary", "invoices", "date.today() > date.fromisoformat", "date.today() >= date.fromisoformat", "a loan due today not being overdue"),
    Mutant("default-directory", "invoices", '"INVOICER_DIR", "invoices"', '"INVOICER_DIR", "output"', "the default directory"),
    Mutant("no-overwrite-warning", "invoices", 'logger.warning("overwriting %s", path)', "pass", "the overwrite warning"),
    Mutant("no-saved-message", "invoices", 'print(f"saved {path}")', "pass", "the saved message"),
    Mutant("usage-exit-code", "cli", 'print("usage: invoicer CUSTOMER", file=sys.stderr)\n        return 2', 'print("usage: invoicer CUSTOMER", file=sys.stderr)\n        return 0', "the usage exit code"),
    Mutant("usage-on-stdout", "cli", 'print("usage: invoicer CUSTOMER", file=sys.stderr)', 'print("usage: invoicer CUSTOMER")', "usage going to stderr"),
    Mutant("error-exit-code", "cli", 'print(f"error: {exc}", file=sys.stderr)\n        return 2', 'print(f"error: {exc}", file=sys.stderr)\n        return 1', "the input error exit code"),
    Mutant("no-save", "cli", "save_invoice(invoice)\n", "\n", "the CLI saving the invoice"),
    Mutant("blank-lines", "cli", "for line in sys.stdin if line.strip()]", "for line in sys.stdin]", "blank input lines being skipped"),
]  # fmt: skip


@dataclass(frozen=True)
class Run:
    """The outcome of one pytest run in a sandbox."""

    code: int
    output: str
    seconds: float
    sandbox: Path


def run_suite(
    tmp_path: Path, *args: str, edit: tuple[str, str, str] | None = None, env: dict[str, str] | None = None
) -> Run:
    """Copy the original package and the learner's tests into a sandbox, apply one edit, and run pytest."""
    sandbox = tmp_path / "sandbox"
    shutil.copytree(PRISTINE, sandbox / "invoicer", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(LEARNER / "tests", sandbox / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    (sandbox / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (sandbox / "guard_plugin.py").write_text(GUARD_PLUGIN, encoding="utf-8")
    (sandbox / "reverse_plugin.py").write_text(REVERSE_PLUGIN, encoding="utf-8")
    if edit is not None:
        module, old, new = edit
        target = sandbox / "invoicer" / f"{module}.py"
        source = target.read_text(encoding="utf-8")
        assert old in source, f"grader bug: {old!r} is not in {module}.py"
        target.write_text(source.replace(old, new, 1), encoding="utf-8")
    clean = {k: v for k, v in os.environ.items() if not k.startswith(("INVOICER_", "PRACTICUM_"))}
    clean |= {"PYTHONPATH": str(sandbox), "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-q",
        "--tb=short",
        "-p",
        "no:cacheprovider",
        "-p",
        "guard_plugin",
        *args,
    ]
    started = time.perf_counter()
    done = subprocess.run(command, cwd=sandbox, env=clean, capture_output=True, text=True, timeout=120, check=False)
    return Run(done.returncode, done.stdout + done.stderr, time.perf_counter() - started, sandbox)


def test_your_suite_passes_on_the_original_code(tmp_path: Path) -> None:
    result = run_suite(tmp_path)
    assert result.code == 0, (
        f"your suite must pass on the original code (exit code 5 means no tests yet):\n{result.output}"
    )


def test_your_suite_is_fast(tmp_path: Path) -> None:
    result = run_suite(tmp_path)
    assert result.code == 0, result.output
    assert result.seconds < MAX_SECONDS, (
        f"took {result.seconds:.1f}s: patch time.sleep so that retries never really wait"
    )


def test_your_suite_covers_the_package(tmp_path: Path) -> None:
    result = run_suite(tmp_path, "--cov=invoicer", f"--cov-fail-under={MIN_COVERAGE}", "--cov-report=term-missing")
    assert result.code == 0, f"coverage must reach {MIN_COVERAGE}%:\n{result.output}"


def test_your_suite_ignores_the_machines_environment(tmp_path: Path) -> None:
    polluted = {"INVOICER_CURRENCY": "JPY", "INVOICER_TAX": "0.5", "INVOICER_DIR": str(tmp_path / "polluted")}
    result = run_suite(tmp_path, env=polluted)
    assert result.code == 0, (
        f"your tests depend on environment variables set on this machine. Use delenv:\n{result.output}"
    )
    assert not (tmp_path / "polluted").exists(), "a test wrote to the machine's INVOICER_DIR. Set it to a tmp_path"


def test_your_suite_ignores_the_real_date(tmp_path: Path) -> None:
    edit = ("invoices", "from datetime import date, timedelta\n", OTHER_CLOCK)
    result = run_suite(tmp_path, edit=edit)
    assert result.code == 0, f"your tests depend on the real date. Replace invoices.date:\n{result.output}"


def test_your_tests_do_not_depend_on_order(tmp_path: Path) -> None:
    result = run_suite(tmp_path, "-p", "reverse_plugin")
    assert result.code == 0, f"your suite fails when run in reverse order, so tests share state:\n{result.output}"


def test_your_suite_leaves_no_files_behind(tmp_path: Path) -> None:
    result = run_suite(tmp_path)
    assert result.code == 0, result.output
    assert not (result.sandbox / "invoices").exists(), (
        "a test wrote to ./invoices. Use tmp_path with INVOICER_DIR or chdir"
    )


@pytest.mark.parametrize("mutant", MUTANTS, ids=lambda m: m.id)
def test_your_suite_catches(tmp_path: Path, mutant: Mutant) -> None:
    result = run_suite(tmp_path, "-x", edit=(mutant.module, mutant.old, mutant.new))
    assert result.code == 1, (
        f"planted bug survived or crashed collection (exit {result.code}). Test {mutant.hint}.\n{result.output[-1500:]}"
    )
