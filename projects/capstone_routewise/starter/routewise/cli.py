"""Command-line interface: ``routewise generate | plan | report``."""

import argparse
import sys  # noqa: F401
from collections.abc import Sequence
from pathlib import Path

from routewise.assign import METHODS, plan_routes  # noqa: F401
from routewise.data import generate_city, load_city, save_city  # noqa: F401
from routewise.eta import simulate_deliveries  # noqa: F401
from routewise.report import render_report  # noqa: F401
from routewise.routing import Instance, check_plan, plan_cost  # noqa: F401
from routewise.store import PlanNotFoundError, Store  # noqa: F401


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with its three subcommands."""
    parser = argparse.ArgumentParser(prog="routewise", description="Plan bakery delivery routes.")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="generate a synthetic city as CSV files")
    gen.add_argument("--customers", type=int, default=40, help="number of customers")
    gen.add_argument("--seed", type=int, default=0, help="random seed")
    gen.add_argument("--out", type=Path, required=True, help="output directory")

    plan = sub.add_parser("plan", help="plan routes for a city and store them")
    plan.add_argument("--city", type=Path, required=True, help="directory written by `generate`")
    plan.add_argument("--db", type=Path, required=True, help="SQLite database file")
    plan.add_argument("--capacity", type=float, default=60.0, help="crates per van")
    plan.add_argument("--method", choices=METHODS, default="savings", help="construction heuristic")
    plan.add_argument("--no-improve", action="store_true", help="skip 2-opt")
    plan.add_argument("--simulate", action="store_true", help="also simulate and store actual deliveries")
    plan.add_argument("--seed", type=int, default=0, help="seed for the simulation")

    report = sub.add_parser("report", help="report KPIs for a stored plan")
    report.add_argument("--city", type=Path, required=True, help="directory written by `generate`")
    report.add_argument("--db", type=Path, required=True, help="SQLite database file")
    report.add_argument("--plan", type=int, default=None, help="plan id (default: the latest)")
    report.add_argument("--format", choices=("markdown", "text"), default="markdown", help="output format")
    report.add_argument("--out", type=Path, default=None, help="write the report to a file instead of stdout")
    return parser


def _generate(args: argparse.Namespace) -> int:
    # TODO: implement this function.
    raise NotImplementedError


def _plan(args: argparse.Namespace) -> int:
    # TODO: implement this function.
    raise NotImplementedError


def _report(args: argparse.Namespace) -> int:
    # TODO: implement this function.
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments without the program name; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code.
    """
    args = build_parser().parse_args(argv)
    handlers = {"generate": _generate, "plan": _plan, "report": _report}
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
