"""Milestone 5: charts, the Markdown report, and the end-to-end pipeline."""

from pathlib import Path

import pandas as pd
import pytest
from cityeda.charts import plot_counts, plot_resolution_hist, plot_weekly_trend
from cityeda.generate import write_requests
from cityeda.pipeline import PipelineResult, main, run_pipeline
from cityeda.report import markdown_table

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _is_png(path: Path) -> bool:
    return path.is_file() and path.read_bytes()[:8] == PNG_MAGIC and path.stat().st_size > 1000


@pytest.fixture(scope="module")
def run(tmp_path_factory: pytest.TempPathFactory) -> PipelineResult:
    base = tmp_path_factory.mktemp("pipeline")
    csv_path = write_requests(base / "requests.csv", 2000, seed=311)
    return run_pipeline(csv_path, base / "out")


def test_plot_counts_writes_png(tmp_path: Path) -> None:
    path = plot_counts(pd.Series({"a": 3, "b": 1}), tmp_path / "nested" / "c.png", title="Counts")
    assert path == tmp_path / "nested" / "c.png", "return the path written"
    assert _is_png(path), "plot_counts must save a real PNG (creating parent folders)"


def test_plot_weekly_trend_writes_png(tmp_path: Path) -> None:
    index = pd.date_range("2025-01-06", periods=6, freq="W-MON")
    trend = pd.DataFrame({"requests": [5, 7, 6, 9, 8, 10], "rolling_mean": [5, 6, 6, 6.75, 7.5, 8.25]}, index=index)
    assert _is_png(plot_weekly_trend(trend, tmp_path / "t.png")), "weekly trend PNG"


def test_plot_resolution_hist_writes_png(tmp_path: Path) -> None:
    frame = pd.DataFrame({"resolution_hours": [1.0, 2.0, 30.0, None, 900.0], "is_outlier": [False] * 4 + [True]})
    assert _is_png(plot_resolution_hist(frame, tmp_path / "h.png")), "histogram PNG"


def test_markdown_table() -> None:
    table = markdown_table(["A", "B"], [[1, "x"], [2, "y"]])
    assert table.splitlines() == ["| A | B |", "|---|---|", "| 1 | x |", "| 2 | y |"], "GitHub-style table"
    with pytest.raises(ValueError):
        markdown_table(["A"], [[1, 2]])


def test_pipeline_writes_files(run: PipelineResult) -> None:
    assert run.report_path.name == "report.md" and run.report_path.is_file(), "report.md in the output folder"
    assert set(run.chart_paths) == {"category", "borough", "trend", "resolution"}, "four named charts"
    for name, path in run.chart_paths.items():
        assert _is_png(path), f"{name} chart must be a PNG"
        assert path.parent == run.report_path.parent / "charts", "charts live in out/charts/"


def test_report_sections(run: PipelineResult) -> None:
    text = run.report_path.read_text(encoding="utf-8")
    for heading in (
        "# 311 Service Requests",
        "## Summary",
        "## Data cleaning",
        "## Requests by category",
        "## Requests by borough",
        "## Resolution time",
        "## Weekly trend",
        "## Bronx vs Manhattan",
    ):
        assert heading in text, f"report is missing the heading {heading!r}"


def test_report_links_every_chart(run: PipelineResult) -> None:
    text = run.report_path.read_text(encoding="utf-8")
    for path in run.chart_paths.values():
        assert f"](charts/{path.name})" in text, f"report must embed charts/{path.name} with a relative link"


def test_report_contains_computed_numbers(run: PipelineResult) -> None:
    text = run.report_path.read_text(encoding="utf-8")
    assert "2,040" in text and "1,980" in text, "raw and cleaned row counts"
    assert "drop_duplicate_ids" in text and "| 40 |" in text, "the cleaning log appears as a table"
    assert "25.2 hours" in text, "the median resolution time"
    assert "statistically significant" in text, "the borough test is interpreted in words"


def test_pipeline_is_deterministic(tmp_path: Path) -> None:
    csv_path = write_requests(tmp_path / "requests.csv", 400, seed=9)
    first = run_pipeline(csv_path, tmp_path / "one").report_path.read_text(encoding="utf-8")
    second = run_pipeline(csv_path, tmp_path / "two").report_path.read_text(encoding="utf-8")
    assert first == second, "the same input must produce the same report"


def test_main_generates_and_reports(tmp_path: Path) -> None:
    assert main(["--out", str(tmp_path / "cli"), "-n", "300", "--seed", "4"]) == 0, "main returns exit code 0"
    assert (tmp_path / "cli" / "requests.csv").is_file(), "main writes the generated CSV when --csv is omitted"
    assert (tmp_path / "cli" / "report.md").is_file(), "main writes the report"
