"""Command-line interface and composition root.

Output policy: command *results* (lists, stats, exports) are written to standard output with
``sys.stdout.write`` so they can be piped into other tools. Diagnostics are structlog events on
standard error. Library modules never write to either stream directly.

Run it with ``pixi run python -m habits <command>`` from your project directory.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import structlog

from habits.domain import HabitError
from habits.logging_config import configure_logging
from habits.ports import Clock, FixedClock, SystemClock
from habits.service import HabitService
from habits.sqlite_repo import SqliteRepository

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
    match args.command:
        case "add":
            habit = service.create_habit(args.name, args.frequency)
            return f"created {habit.id} ({habit.frequency})\n"
        case "checkin":
            new = service.check_in(args.habit_id, args.day)
            return f"checked in {args.habit_id}\n" if new else f"{args.habit_id} already done this period\n"
        case "undo":
            removed = service.undo(args.habit_id, args.day)
            return f"undid {args.habit_id}\n" if removed else f"nothing to undo for {args.habit_id}\n"
        case "archive":
            service.archive_habit(args.habit_id)
            return f"archived {args.habit_id}\n"
        case "list":
            habits = service.list_habits(include_archived=args.all)
            if not habits:
                return "no habits yet; add one with: habits add NAME\n"
            lines = [f"{h.id}\t{h.name}\t{h.frequency}{'\tarchived' if h.archived else ''}" for h in habits]
            return "\n".join(lines) + "\n"
        case "stats":
            s = service.stats(args.habit_id, args.start, args.end)
            return (
                f"habit: {s.habit_id}\ncurrent_streak: {s.current_streak}\nlongest_streak: {s.longest_streak}\n"
                f"completed: {s.completed}/{s.periods}\ncompletion_rate: {s.completion_rate:.1%}\n"
            )
        case _:
            text = service.export_csv() if args.format == "csv" else service.export_json()
            if args.output is None:
                return text
            args.output.write_text(text, encoding="utf-8")
            return f"exported to {args.output}\n"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name (default ``sys.argv[1:]``).

    Returns:
        The process exit code: 0 on success, 1 for a habit error. Usage errors exit with 2 via argparse.
    """
    args = build_parser().parse_args(argv)
    configure_logging(verbose=args.verbose)
    db_path = args.db or Path(os.environ.get("HABITS_DB", DEFAULT_DB))
    clock: Clock = FixedClock(args.today) if args.today else SystemClock()
    with SqliteRepository(db_path) as repository:
        try:
            output = _run(args, HabitService(repository, clock))
        except HabitError as exc:
            log.warning("command_failed", command=args.command, error=str(exc))
            sys.stderr.write(f"error: {exc}\n")
            return 1
    sys.stdout.write(output)
    return 0
