"""Wire extract, validate, transform, and load into a DAG and run it incrementally."""

import argparse
import json
import sqlite3
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

import structlog

from etl.dag import DAG, Results
from etl.extract import Manifest, discover_new_files, read_station_file, read_trip_file, snapshot_date
from etl.models import RawRow, RunSummary
from etl.transform import transform
from etl.validate import default_rules, reason_counts, validate, write_rejection_report
from etl.warehouse import (
    apply_station_snapshot,
    connect,
    current_stations,
    get_watermark,
    load_trips,
    set_watermark,
    table_count,
)

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
    manifest = Manifest.load(state_dir / "manifest.json")
    dag = DAG()

    def stations(_: Results) -> list[str]:
        names = []
        for path in discover_new_files(raw_dir, manifest, "stations_*.csv"):
            apply_station_snapshot(conn, read_station_file(path), date.fromisoformat(snapshot_date(path)))
            names.append(path.name)
        return names

    def extract(_: Results) -> tuple[list[str], list[RawRow]]:
        files = discover_new_files(raw_dir, manifest, "trips_*")
        rows = [row for path in files for row in read_trip_file(path)]
        return [p.name for p in files], rows

    def check(results: Results) -> Any:
        _, rows = results["extract"]
        known = {r[0] for r in conn.execute("SELECT DISTINCT station_id FROM dim_station")}
        outcome = validate(rows, default_rules(known))
        write_rejection_report(outcome.rejected, state_dir / "rejected.jsonl")
        return outcome

    def shape(results: Results) -> Any:
        return transform(results["validate"].valid, current_stations(conn))

    def load(results: Results) -> tuple[int, int, str | None]:
        trips, _ = results["transform"]
        previous = get_watermark(conn)
        late = sum(1 for t in trips if previous is not None and t.start_utc.isoformat() <= previous)
        loaded = load_trips(conn, trips)
        watermark = previous
        if trips:
            watermark = set_watermark(conn, max(t.start_utc for t in trips).isoformat())
        for name in [*results["stations"], *results["extract"][0]]:
            manifest.mark(name)
        manifest.save()
        return loaded, late, watermark

    def summary(results: Results) -> RunSummary:
        files, rows = results["extract"]
        outcome = results["validate"]
        _, removed = results["transform"]
        loaded, late, watermark = results["load"]
        return RunSummary(
            files_processed=[*results["stations"], *files],
            rows_read=len(rows),
            rows_valid=len(outcome.valid),
            rows_rejected=len(outcome.rejected),
            rejected_by_reason=reason_counts(outcome.rejected),
            duplicates_removed=removed,
            late_records=late,
            trips_loaded=loaded,
            fact_trip_rows=table_count(conn, "fact_trip"),
            station_versions=table_count(conn, "dim_station"),
            watermark=watermark,
        )

    dag.add("stations", stations, retries=1)
    dag.add("extract", extract, deps=("stations",), retries=2)
    dag.add("validate", check, deps=("extract",))
    dag.add("transform", shape, deps=("validate",))
    dag.add("load", load, deps=("transform",), retries=1)
    dag.add("summary", summary, deps=("load",))
    return dag


def run_pipeline(raw_dir: Path, db_path: Path, state_dir: Path) -> RunSummary:
    """Run one incremental pipeline pass over any raw files not yet processed.

    Args:
        raw_dir: Raw files directory.
        db_path: Warehouse database file (created if missing).
        state_dir: Directory for ``manifest.json`` and ``rejected.jsonl``.

    Returns:
        The run summary.
    """
    conn = connect(db_path)
    try:
        summary: RunSummary = build_dag(raw_dir, conn, state_dir).run()["summary"]
    finally:
        conn.close()
    log.info("pipeline_finished", **asdict(summary))
    return summary


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point: ``pixi run python -m etl.pipeline RAW_DIR DB STATE_DIR [--generate]``.

    Args:
        argv: Arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="Run the bike-share ETL pipeline.")
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("db", type=Path)
    parser.add_argument("state_dir", type=Path)
    parser.add_argument("--generate", action="store_true", help="write sample raw files first")
    args = parser.parse_args(argv)
    if args.generate:
        from etl.generator import generate

        generate(args.raw_dir)
    summary = run_pipeline(args.raw_dir, args.db, args.state_dir)
    print(json.dumps(asdict(summary), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
