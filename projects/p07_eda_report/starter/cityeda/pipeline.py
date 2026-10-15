"""End-to-end pipeline: load, clean, engineer features, analyze, chart, and report."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import structlog

from cityeda.clean import CleaningStep
from cityeda.generate import write_requests

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """What one pipeline run produced.

    Attributes:
        frame: The cleaned, featured frame.
        log: The cleaning log.
        report_path: The Markdown report.
        chart_paths: PNG files keyed by chart name.
    """

    frame: pd.DataFrame
    log: list[CleaningStep]
    report_path: Path
    chart_paths: dict[str, Path]


def run_pipeline(
    csv_path: Path, out_dir: Path, *, compare: tuple[str, str] = ("Bronx", "Manhattan"), seed: int = 0
) -> PipelineResult:
    """Run every stage and write ``report.md`` plus ``charts/*.png`` into ``out_dir``.

    Args:
        csv_path: Raw CSV to analyze.
        out_dir: Output directory (created if needed).
        compare: The two boroughs to compare.
        seed: Seed for the bootstrap.

    Returns:
        The result of the run.
    """
    # TODO: import what you need from cityeda.load, .clean, .features, .analysis, .charts, and .report.
    # TODO: load -> clean -> add_features -> analysis -> charts in out_dir/'charts' -> ReportData -> write_report.
    #   ReportData.charts holds paths relative to out_dir, such as 'charts/by_category.png'.
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point: ``pixi run python -m cityeda.pipeline --out reports``.

    Args:
        argv: Arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description="Generate (or read) 311 data and write an EDA report.")
    parser.add_argument("--csv", type=Path, help="raw CSV to analyze; generated when omitted")
    parser.add_argument("--out", type=Path, default=Path("reports"), help="output directory")
    parser.add_argument("-n", type=int, default=2000, help="requests to generate")
    parser.add_argument("--seed", type=int, default=311, help="generator seed")
    args = parser.parse_args(argv)
    csv_path = args.csv or write_requests(args.out / "requests.csv", args.n, args.seed)
    result = run_pipeline(csv_path, args.out)
    log.info("report_written", report=str(result.report_path), rows=len(result.frame), charts=len(result.chart_paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
