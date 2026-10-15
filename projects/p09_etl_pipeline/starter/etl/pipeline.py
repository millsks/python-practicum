"""Wire extract, validate, transform, and load into a DAG and run it incrementally."""

import sqlite3
from pathlib import Path

import structlog

from etl.dag import DAG
from etl.models import RunSummary

log = structlog.get_logger(__name__)


def build_dag(raw_dir: Path, conn: sqlite3.Connection, state_dir: Path) -> DAG:
    """Build the pipeline DAG.

    Tasks: ``stations`` → ``extract`` → ``validate`` → ``transform`` → ``load`` → ``summary``. The manifest is saved
    only in ``load``, after the warehouse transaction commits, so a failed run is retried in full next time.

    Args:
        raw_dir: Raw files directory.
        conn: Open warehouse connection (see :func:`etl.warehouse.connect`).
        state_dir: Directory for the manifest and the rejected-rows report.

    Returns:
        The DAG, ready to run.
    """
    # TODO: add tasks stations -> extract -> validate -> transform -> load -> summary (see the README)
    raise NotImplementedError


def run_pipeline(raw_dir: Path, db_path: Path, state_dir: Path) -> RunSummary:
    """Run one incremental pipeline pass over any raw files not yet processed.

    Args:
        raw_dir: Raw files directory.
        db_path: Warehouse database file (created if missing).
        state_dir: Directory for ``manifest.json`` and ``rejected.jsonl``.

    Returns:
        The run summary.
    """
    # TODO: connect, build_dag(...).run()['summary'], always close the connection
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point: ``pixi run python -m etl.pipeline RAW_DIR DB STATE_DIR [--generate]``.

    Args:
        argv: Arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    # TODO: argparse raw_dir db state_dir [--generate]; print the summary as JSON
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
