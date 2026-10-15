"""End-to-end pipeline: load, clean, engineer features, analyze, chart, and report."""

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import structlog

from cityeda.analysis import bootstrap_median_ci, compare_boroughs, requests_by, resolution_summary, weekly_trend
from cityeda.charts import plot_counts, plot_resolution_hist, plot_weekly_trend
from cityeda.clean import CleaningStep, clean_requests
from cityeda.features import add_features
from cityeda.generate import write_requests
from cityeda.load import load_requests
from cityeda.report import ReportData, render_report, write_report

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
    raw = load_requests(csv_path)
    cleaned, cleaning_log = clean_requests(raw)
    df = add_features(cleaned)
    by_category = requests_by(df, "category")
    by_borough = requests_by(df, "borough")
    trend = weekly_trend(df)
    charts_dir = out_dir / "charts"
    chart_paths = {
        "category": plot_counts(by_category, charts_dir / "by_category.png", title="Requests by category"),
        "borough": plot_counts(by_borough, charts_dir / "by_borough.png", title="Requests by borough"),
        "trend": plot_weekly_trend(trend, charts_dir / "weekly_trend.png"),
        "resolution": plot_resolution_hist(df, charts_dir / "resolution_hours.png"),
    }
    data = ReportData(
        raw_rows=len(raw),
        clean_rows=len(df),
        log=cleaning_log,
        by_category=by_category,
        by_borough=by_borough,
        median=bootstrap_median_ci(df["resolution_hours"], seed=seed),
        resolution_by_category=resolution_summary(df),
        trend=trend,
        comparison=compare_boroughs(df, *compare),
        charts={name: path.relative_to(out_dir).as_posix() for name, path in chart_paths.items()},
    )
    report_path = write_report(render_report(data), out_dir / "report.md")
    return PipelineResult(df, cleaning_log, report_path, chart_paths)


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
