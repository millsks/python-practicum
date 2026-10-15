# Project 7: City Data EDA Report

## Scenario

The city's 311 office (the non-emergency line for noise, heat, potholes, broken street lights) wants a repeatable
exploratory report on its service requests. The raw export is messy: borough names arrive as `BROOKLYN`, `Bklyn`, and
`The Bronx`; some rows have blank boroughs; dates are sometimes `not a date` or `31/02/2025`; a few requests "close"
before they open; some take thousands of hours; and the export repeats some request IDs.

You will build `cityeda`, a small pandas pipeline that turns that export into a cleaned dataset, a set of charts, and
a Markdown report a city manager can read, with every cleaning decision documented.

## What you build

| Module | Responsibility |
|---|---|
| `generate.py` | **Provided.** `generate_requests(n, seed)` makes a deterministic raw CSV with known mess. |
| `load.py` | `load_requests(path)` reads the CSV with explicit dtypes (no type guessing). |
| `clean.py` | `clean_requests(raw)` applies seven documented rules and returns `(frame, cleaning_log)`. |
| `features.py` | `add_features(df)` adds `resolution_hours`, `weekday`, `hour`, `week`, `is_outlier`. |
| `analysis.py` | Counts by category/borough, per-category summary, bootstrap CI for the median, weekly trend with a rolling mean, Mann-Whitney U borough comparison. |
| `charts.py` | Three chart functions that save PNGs with `matplotlib.figure.Figure` (no GUI needed). |
| `report.py` | `markdown_table`, `render_report`, `write_report`. |
| `pipeline.py` | `run_pipeline(csv, out_dir)` and a `main()` CLI that logs with structlog. |

## Getting started

```bash
pixi run start p07          # copies the starter into work/p07_eda_report/
pixi run grade p07          # runs the tests against your work/ copy
```

Run your pipeline end to end from `work/p07_eda_report/`:

```bash
pixi run python -m cityeda.pipeline --out reports
```

## Milestones

1. **Load** (`test_cityeda_load.py`): explicit dtypes, categorical `channel`/`status`, a clear error for missing columns.
2. **Clean** (`test_cityeda_clean.py`): the seven rules in order, each logged with how many rows it touched.
3. **Features** (`test_cityeda_features.py`): durations, calendar features, per-category IQR outliers.
4. **Analyze** (`test_cityeda_analysis.py`): exact counts and medians on the seed-311 dataset, a deterministic
   bootstrap, a 26-week trend, and the borough test matching `scipy.stats.mannwhitneyu`.
5. **Report** (`test_cityeda_outputs.py`): PNG files, a Markdown report with every section and chart link, and a
   deterministic end-to-end run.

## Stretch goals

- Localize timestamps to `America/New_York` and handle the daylight-saving gap.
- Add a heatmap of requests by weekday and hour.
- Compare all borough pairs and correct for multiple comparisons (Holm-Bonferroni).
- Port `clean_requests` to Polars and compare timings (see M52).
- Render the Markdown report to HTML.
