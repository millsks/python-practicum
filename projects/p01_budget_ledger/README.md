# Project 1: Budget Ledger CLI

Closes Part 1 (Foundations). You build `ledger`, a small command-line tool that reads the CSV files your bank
lets you download, sorts every transaction into a category using keyword rules, totals each month, spots charges
that were imported twice, warns you when a category went over budget, and exports a report.

The full brief with diagrams, milestones, and the rubric is on the course site: `docs/projects/p01-budget-ledger.html`.

## Scenario

You downloaded a few months of checking-account exports. Each bank formats them slightly differently: the header
may be `Date` or `DATE`, dates may be `2026-01-05` or `01/05/2026`, amounts may be `-1,450.00` or `(1450.00)`, and
some exports have a byte-order mark at the start. One file contains a corrupt row. You want one honest answer to
"where did my money go each month, and where did I overspend?"

## What you practise

| Module | Used for |
|---|---|
| M05 Functions | small, pure, documented functions with type hints |
| M06 Collections | dicts of dicts, grouping with `setdefault`/`defaultdict`, sorting, tuples as keys |
| M07 Exceptions | one custom `LedgerError`, chaining with `raise ... from exc`, exit codes |
| M08 Modules | a package split into modules, `__main__.py`, running with `pixi run python -m ledger` |
| M09 Files | `pathlib`, `csv.DictReader`/`csv.writer`, `json` with a `default=` encoder, `tomllib` |

## About the dataclasses (a preview of Part 2)

`ledger/models.py` is **already written for you**. It uses `@dataclass`, which you meet properly in M13. For now,
read a dataclass as "a named bundle of fields":

```python
from ledger.models import Transaction

t = Transaction(date(2026, 1, 2), "Whole Foods", Decimal("-84.17"))
t.amount  # Decimal('-84.17')
t.month  # '2026-01'  (a computed property)
t.category  # 'uncategorized' (a default value)
```

`frozen=True` means you cannot change a field after creation; to get a modified copy use
`dataclasses.replace(t, category="groceries")`. `Rule`, `Config`, and `Overrun` work the same way. `LedgerError` in `errors.py` is provided too, so you write no
classes at all: everything you implement is a function.

Money uses `decimal.Decimal`, never `float`, because `0.1 + 0.2 != 0.3` in binary floating point (M02).

## Files

```
starter/ledger/
  __init__.py   public API (provided)
  __main__.py   lets `python -m ledger` run the CLI (provided)
  errors.py     LedgerError (provided)
  models.py     Transaction, Rule, Config, Overrun (provided)
  parsing.py    Milestone 1: parse_amount, parse_date, parse_row, read_transactions, read_many
  rules.py      Milestone 2: load_config, categorize, categorize_all
  analysis.py   Milestone 3: monthly_summary, find_duplicates, check_budgets
  report.py     Milestone 4: build_report, write_json, write_summary_csv, export_report
  cli.py        Milestone 5: build_parser, main
sample/         two bank exports and a rules.toml to try the tool on
tests/          the grading tests, one file per milestone
```

## Start and grade

```bash
pixi run projects            # list projects
pixi run start p01           # copies starter/ to work/p01_budget_ledger/
pixi run grade p01           # runs the tests against work/p01_budget_ledger/
pixi run grade p01 -k parsing   # only the Milestone 1 tests
```

Edit the files in `work/p01_budget_ledger/ledger/`. Every function body starts as `raise NotImplementedError` with
`TODO` comments that point the way. Work through the milestones in order; each has its own test file.

Try your tool on the samples (from `work/p01_budget_ledger/`):

```bash
pixi run python -m ledger summary ../../projects/p01_budget_ledger/sample/checking-2026-01.csv --rules ../../projects/p01_budget_ledger/sample/rules.toml
pixi run python -m ledger duplicates ../../projects/p01_budget_ledger/sample/checking-2026-01.csv
pixi run python -m ledger budget ../../projects/p01_budget_ledger/sample/checking-2026-01.csv --rules ../../projects/p01_budget_ledger/sample/rules.toml
pixi run python -m ledger export ../../projects/p01_budget_ledger/sample/checking-2026-01.csv --rules ../../projects/p01_budget_ledger/sample/rules.toml --out report.json
```

`checking-2026-02.csv` contains a deliberately broken row; your tool should refuse it with a message naming
`checking-2026-02.csv:7`.

## Requirements

1. **Parsing.** Read CSVs with `Date`, `Description`, `Amount` columns (any case, any order, extra columns ignored,
   BOM tolerated). Dates are `YYYY-MM-DD` or `MM/DD/YYYY`. Amounts allow `$`, commas, a minus sign, or parentheses.
   Any malformed row raises `LedgerError` whose message starts with `file.csv:LINE:`.
2. **Rules.** `load_config` reads `[rules]` and `[budgets]` from `.toml` or `.json`. Keywords match
   case-insensitively as substrings; the first matching rule wins; no match gives `"uncategorized"`.
3. **Summaries.** `monthly_summary` returns `{"YYYY-MM": {category: Decimal total}}`, sorted.
4. **Duplicates.** Same date, same amount, and same description ignoring case and extra spaces.
5. **Budgets.** Spending is the negated category total; an overrun is spending strictly above the limit.
6. **Export.** `.json` writes the full report (money and dates as strings); `.csv` writes `month,category,total`.
7. **CLI.** `main(argv) -> int` with subcommands `summary`, `duplicates`, `budget`, `export`. Exit codes: `0` ok,
   `1` data error (message on stderr), `2` usage error, `3` budget overrun found.
8. **Quality.** Standard library only, type hints and Google-style docstrings on public functions, no bare
   `except`, library functions return values and never print (only `cli.py` prints).

## Milestones

1. Parsing (`tests/test_ledger_parsing.py`)
2. Rules and categorization (`tests/test_ledger_rules.py`)
3. Summaries, duplicates, budgets (`tests/test_ledger_analysis.py`)
4. Reports and export (`tests/test_ledger_report.py`)
5. The CLI (`tests/test_ledger_cli.py`)

## Stretch goals

- `--skip-bad-rows`: warn about malformed rows on stderr instead of stopping (count them in the report).
- Support banks that export separate `Debit` and `Credit` columns instead of a signed `Amount`.
- Regular-expression rules (`re.search`) alongside plain keywords.
- A `months` subcommand that compares two months side by side, with percentage change per category.
- Add a `ledger` entry in your own `pixi.toml` `[tasks]` table so `pixi run ledger summary ...` works.
