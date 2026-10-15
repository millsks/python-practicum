# Project 6: Habit Tracker Service

Part 6 · Professional Python. The full brief with diagrams, hints, and the rubric is on the course site at
`docs/projects/p06-habit-tracker.html` (`pixi run serve`).

## Scenario

You are building the back end of a habit tracker that a small team will maintain for years. It has to be correct
about dates (streaks are the feature users care about most), safe with their data, and easy to change. You will
build it as a layered application: a pure **domain**, **ports** (Protocols), two **adapters** (in-memory and SQLite),
a **service layer** of use cases, and an **argparse CLI** that wires everything together and logs with structlog.

## Requirements

| Layer | Module | What it must do |
|---|---|---|
| Domain | `habits/domain.py` | `Frequency` (daily, weekly per ISO week, specific weekdays) with `parse`, `__str__`, `period_start`, `is_due`, `periods`, `previous_period`; `Habit.create` (validated name, slug id); `Completion`; streaks (`current_streak`, `longest_streak`), `completion_rate`, `compute_stats` |
| Ports | `habits/ports.py` | `HabitRepository` and `Clock` Protocols (given); `SystemClock` and `FixedClock` |
| Adapters | `habits/memory.py`, `habits/sqlite_repo.py` | `InMemoryRepository`; `SqliteRepository` with migrations recorded in a `schema_version` table, one transaction per write, parameterized queries only |
| Service | `habits/service.py` | `HabitService`: create/archive/list, `check_in` (idempotent per period), `undo`, `stats`, `export_json`, `export_csv` |
| CLI | `habits/cli.py` | `habits add/checkin/undo/archive/list/stats/export` with `--db`, `--today`, `-v` |

Rules that the tests check:

- A check-in on a day whose period already has one returns `False` and stores nothing.
- Leaving *today's* period unchecked does not break the current streak; missing a finished period does.
- Check-ins before the habit was created, on days that are not due, or in the future are rejected (or ignored by the
  streak math).
- Logs are structlog `key=value` lines on **stderr**. Command results go to **stdout** via `sys.stdout.write`, so
  `habits export --format json > backup.json` produces a clean file. Library modules never write to either stream.

## Start and grade

```bash
pixi run start p06            # copies starter/ to work/p06_habit_tracker/
pixi run grade p06            # runs the tests against your work/ copy
pixi run practicum grade p06 -k domain   # just one milestone (the tests are grouped by file)
```

Try your CLI from the work directory:

```bash
cd work/p06_habit_tracker
pixi run python -m habits --db demo.db add "Drink water"
pixi run python -m habits --db demo.db checkin drink-water
pixi run python -m habits --db demo.db stats drink-water
pixi run python -m habits --db demo.db export --format csv
```

## Milestones

1. **Domain** (`tests/test_habits_domain.py`): frequencies, habits, streaks, completion rates. Pure functions only.
2. **Repositories** (`tests/test_habits_repository.py`): contract tests run against *both* adapters through one
   parametrized fixture, plus SQLite migrations, rollback, and injection safety.
3. **Service** (`tests/test_habits_service.py`): use cases with a `FixedClock`, so "today" is under test control.
4. **CLI** (`tests/test_habits_cli.py`): argparse, exit codes, stdout vs stderr, real SQLite files in `tmp_path`.

## Stretch goals

- Add a `rename` use case and a migration that adds a `notes` column.
- Add a "times per week" frequency (for example 3x weekly) and its streak rules.
- Add a `JsonFileRepository` adapter and run the contract tests against it too.
- Put a FastAPI front end (Module 45) on the same `HabitService`, without touching the domain.
