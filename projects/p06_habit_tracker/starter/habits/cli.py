"""Command-line interface and composition root.

Output policy: command *results* (lists, stats, exports) are written to standard output with
``sys.stdout.write`` so they can be piped into other tools. Diagnostics are structlog events on
standard error. Library modules never write to either stream directly.

Run it with ``pixi run python -m habits <command>`` from your project directory.
"""

# Imports the reference solution also uses (add them back as you need them):
#   os, sys, habits.domain.HabitError, habits.logging_config.configure_logging, habits.ports.Clock, habits.ports.FixedClock, habits.ports.SystemClock, habits.sqlite_repo.SqliteRepository
from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import structlog

from habits.service import HabitService

log = structlog.get_logger(__name__)

DEFAULT_DB = "habits.db"


def _iso_date(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a date like 2026-01-31, got {text!r}") from None


def build_parser() -> argparse.ArgumentParser:
    """Build the ``habits`` argument parser.

    Returns:
        The parser with all subcommands.
    """
    parser = argparse.ArgumentParser(prog="habits", description="Track habits, streaks, and completion rates.")
    parser.add_argument("--db", type=Path, help=f"database file (default $HABITS_DB or {DEFAULT_DB})")
    parser.add_argument("--today", type=_iso_date, help="pretend today is this date (for backfilling and tests)")
    parser.add_argument("-v", "--verbose", action="store_true", help="log info events to stderr")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="create a habit")
    add.add_argument("name")
    add.add_argument("-f", "--frequency", default="daily", help="daily, weekly, or days such as mon,wed,fri")
    for name, text in (("checkin", "mark a habit done"), ("undo", "remove the check-in for a period")):
        sub = commands.add_parser(name, help=text)
        sub.add_argument("habit_id")
        sub.add_argument("--date", type=_iso_date, dest="day", help="day of the check-in (default today)")
    archive = commands.add_parser("archive", help="archive a habit")
    archive.add_argument("habit_id")
    listing = commands.add_parser("list", help="list habits")
    listing.add_argument("--all", action="store_true", help="include archived habits")
    stats = commands.add_parser("stats", help="show streaks and completion rate")
    stats.add_argument("habit_id")
    stats.add_argument("--from", type=_iso_date, dest="start", help="first day (default 29 days before --to)")
    stats.add_argument("--to", type=_iso_date, dest="end", help="last day (default today)")
    export = commands.add_parser("export", help="export all habits")
    export.add_argument("--format", choices=("csv", "json"), default="json")
    export.add_argument("-o", "--output", type=Path, help="write to a file instead of stdout")
    return parser


def _run(args: argparse.Namespace, service: HabitService) -> str:
    # TODO: dispatch on args.command (match/case) and return the text to write to stdout.
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name (default ``sys.argv[1:]``).

    Returns:
        The process exit code: 0 on success, 1 for a habit error. Usage errors exit with 2 via argparse.
    """
    # TODO: parse args, configure_logging(verbose=...), pick the db (--db, $HABITS_DB, or DEFAULT_DB) and the
    # TODO: clock (FixedClock for --today), run the command, catch HabitError -> stderr 'error: ...' and return 1.
    raise NotImplementedError
