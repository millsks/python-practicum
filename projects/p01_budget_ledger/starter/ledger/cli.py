"""Command-line interface: ``pixi run python -m ledger <command> ...``.

Milestone 5. Tests: ``tests/test_ledger_cli.py``.
"""

import argparse
import sys  # noqa: F401
from collections.abc import Sequence

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_OVER_BUDGET = 3


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with its four subcommands.

    Every subcommand takes one or more CSV paths (``nargs="+"``, ``type=Path``) and an optional ``--rules PATH``.

    * ``summary [--month YYYY-MM]`` prints totals per month and category.
    * ``duplicates`` prints each duplicate group with its ``file:line`` locations and a final
      ``"N duplicate group(s)"`` line.
    * ``budget`` prints each overrun; it needs ``--rules``.
    * ``export --out PATH`` (required) writes a ``.json`` report or ``.csv`` summary.

    Returns:
        The configured parser.
    """
    # TODO: parser.add_subparsers(dest="command", required=True), then one add_parser per command.
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name; ``None`` uses ``sys.argv[1:]``.

    Returns:
        ``0`` on success, ``1`` for a data error, ``2`` for a usage error, ``3`` when ``budget`` finds overruns.
    """
    # TODO: parse_args raises SystemExit(2) on bad arguments: catch it and return its code instead of exiting.
    # TODO: load rules (if given) with load_config, read files with read_many, categorize with categorize_all.
    # TODO: dispatch on args.command to one small function per subcommand.
    # TODO: catch LedgerError, print f"error: {exc}" to sys.stderr, and return EXIT_ERROR.
    # TODO: `summary --month` for a month with no data is a LedgerError; `budget` without --rules is too.
    raise NotImplementedError
