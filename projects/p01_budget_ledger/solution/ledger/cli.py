"""Command-line interface: ``pixi run python -m ledger <command> ...``."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ledger.analysis import check_budgets, find_duplicates, monthly_summary
from ledger.errors import LedgerError
from ledger.models import Config, Transaction
from ledger.parsing import read_many
from ledger.report import export_report
from ledger.rules import categorize_all, load_config

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_OVER_BUDGET = 3


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with its four subcommands.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(prog="ledger", description="Categorize bank exports and check budgets.")
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help_text, description=help_text)
        sub.add_argument("files", nargs="+", type=Path, metavar="CSV", help="bank export CSV file(s)")
        sub.add_argument("--rules", type=Path, help="TOML or JSON file with [rules] and [budgets]")
        return sub

    summary = add("summary", "show totals per month and category")
    summary.add_argument("--month", help="only show this YYYY-MM month")
    add("duplicates", "list transactions that appear more than once")
    add("budget", "report categories over budget (exit status 3 if any)")
    export = add("export", "write a JSON report or CSV summary")
    export.add_argument("--out", type=Path, required=True, help="destination .json or .csv file")
    return parser


def _load(files: Sequence[Path], rules_path: Path | None) -> tuple[list[Transaction], Config]:
    config = load_config(rules_path) if rules_path else Config()
    return categorize_all(read_many(files), config.rules), config


def _cmd_summary(args: argparse.Namespace) -> int:
    transactions, _ = _load(args.files, args.rules)
    summary = monthly_summary(transactions)
    if args.month:
        if args.month not in summary:
            raise LedgerError(f"no transactions in {args.month}")
        summary = {args.month: summary[args.month]}
    for month, categories in summary.items():
        print(month)
        for category, total in categories.items():
            print(f"  {category:<20} {total:>12,.2f}")
    return EXIT_OK


def _cmd_duplicates(args: argparse.Namespace) -> int:
    transactions, _ = _load(args.files, args.rules)
    groups = find_duplicates(transactions)
    for group in groups:
        first = group[0]
        places = ", ".join(f"{t.source}:{t.line}" for t in group)
        print(f"{first.date} {first.description} {first.amount} x{len(group)} ({places})")
    print(f"{len(groups)} duplicate group(s)")
    return EXIT_OK


def _cmd_budget(args: argparse.Namespace) -> int:
    if args.rules is None:
        raise LedgerError("budget needs --rules with a [budgets] section")
    transactions, config = _load(args.files, args.rules)
    overruns = check_budgets(monthly_summary(transactions), config.budgets)
    for o in overruns:
        print(f"{o.month} {o.category}: spent {o.spent:,.2f} of {o.limit:,.2f} (over by {o.over:,.2f})")
    if not overruns:
        print("all categories within budget")
        return EXIT_OK
    return EXIT_OVER_BUDGET


def _cmd_export(args: argparse.Namespace) -> int:
    transactions, config = _load(args.files, args.rules)
    path = export_report(transactions, config.budgets, args.out)
    print(f"wrote {path}")
    return EXIT_OK


COMMANDS = {"summary": _cmd_summary, "duplicates": _cmd_duplicates, "budget": _cmd_budget, "export": _cmd_export}


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name; ``None`` uses ``sys.argv[1:]``.

    Returns:
        ``0`` on success, ``1`` for a data error, ``2`` for a usage error, ``3`` when ``budget`` finds overruns.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    try:
        return COMMANDS[args.command](args)
    except LedgerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
