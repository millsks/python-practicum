# Project 9: ETL Pipeline & Warehouse

**Scenario.** You are the first data engineer at *Spokes*, a city bike-share company. Every night the docking
stations upload a file of the day's trips. The files are messy: some days arrive as CSV with naive local timestamps,
others as JSON Lines with UTC offsets; rows repeat; some timestamps are garbage; some trips reference stations that do
not exist; and trips sometimes arrive a day late. Station names change too, and the analysts want history to stay
correct. Your job: build a pipeline that turns these files into a trustworthy sqlite3 star schema, safely and
repeatably, and answers the first analytics questions.

## Getting started

```bash
pixi run start p09          # copies starter/ to work/p09_etl_pipeline/
pixi run grade p09          # runs the tests against your work/ copy
```

The generator (`etl/generator.py`) and the data types (`etl/models.py`) are complete. Everything else raises
`NotImplementedError` with a `TODO` describing the job. Some imports were trimmed from the starter; add what you need
(`csv`, `json`, `collections.Counter`, `datetime.UTC`, `dataclasses.replace`, `functools`, `graphlib`, ...).

Try the generator first:

```bash
pixi run python -c "from pathlib import Path; from etl.generator import generate; generate(Path('raw'))"
```

## Requirements

| Module | What to build |
|---|---|
| `extract.py` | `Manifest` (processed-files JSON, atomic save), `discover_new_files`, `read_trip_file` (CSV + JSONL to string rows with `_source`), `read_station_file`, `snapshot_date` |
| `validate.py` | `parse_timestamp` (naive = America/New_York, result in UTC), a `Rule` engine, `default_rules`, `validate` (all reasons per row), `reason_counts`, `write_rejection_report` |
| `transform.py` | `normalize` (UTC, `duration_s`, local business `local_date`), `dedupe` on `trip_id`, `enrich` with station names, `transform` |
| `warehouse.py` | `connect` (schema given), `date_key`, `ensure_dates`, SCD2 `apply_station_snapshot`, `current_stations`, point-in-time `station_key_at`, idempotent `load_trips` upsert, `get_watermark` / `set_watermark`, `table_count` |
| `dag.py` | `retry` decorator, `DAG.add`, `DAG.order` (graphlib), `DAG.run` with retries and `TaskFailedError` |
| `analytics.py` | `daily_trips` (7-day moving average with a window function), `top_routes` (`RANK()`) |
| `pipeline.py` | `build_dag`, `run_pipeline` returning a `RunSummary`, `main` CLI |

Rejection reason codes: `missing:<field>`, `bad_timestamp:<field>`, `end_before_start`, `duration_too_long`,
`bad_member_type`, `unknown_station:<field>`, and `bad_json:line<N>`.

## Milestones

1. **Extract** (`test_etl_extract.py`): manifest and readers.
2. **Validate** (`test_etl_validate.py`): rules and reasons.
3. **Transform** (`test_etl_transform.py`): time zones, DST, dedupe, enrichment.
4. **Load** (`test_etl_warehouse.py`): star schema, SCD2, upserts, watermark.
5. **Orchestrate** (`test_etl_dag.py`): DAG order, retries.
6. **End to end** (`test_etl_pipeline.py`): idempotency, incremental runs, late data, analytics.

Run one milestone at a time: `pixi run practicum grade p09 -k extract` (extra arguments go to pytest).

## Stretch goals

- Quarantine table: load rejected rows into `rejected_trip` with the reasons as JSON.
- Allowed lateness: reject trips older than the watermark minus two days with a `too_late` reason.
- Export `fact_trip` to Parquet with DuckDB (`pixi add duckdb`) and query it directly.
- Emit OpenLineage-style lineage events (inputs, outputs, run id) from each DAG task.
