# Project 2: Library Management System

Part 2 capstone. You build the circulation system for the Millbrook Public Library, a small-town library that
still tracks loans on index cards. The package is called `library`.

## Scenario

Millbrook has about 4,000 titles, several copies of the popular ones, and 900 card holders in three tiers
(child, standard, premium). The librarians need software that can:

- catalog books by ISBN, rejecting typos by checking the ISBN check digit;
- track each physical copy and whether it is on the shelf, on loan, or waiting on the hold shelf;
- lend copies with due dates and loan limits that depend on the member's tier;
- charge late fines (25 cents per day, capped at $10 per loan) and block borrowing once fines reach $5;
- keep a first-come, first-served waiting list (a `collections.deque`) for titles with no free copy;
- notify members when a hold is ready, when a fine is charged, and when a loan is overdue;
- search the catalog by title and author keywords;
- save everything to a JSON file and load it back.

## Requirements

- Python 3.14 run through Pixi. No third-party runtime dependencies.
- Dataclasses for records (`Book` is frozen), `Enum`/`StrEnum` for tiers and copy status, a `Protocol` for the
  clock and for the notifier, custom exceptions deriving from `LibraryError`, properties and dunder methods
  (`__str__`, `__len__`, `__contains__`).
- Full type hints; the solution passes `mypy --strict`.
- Dates come from an injectable clock, so tests can move time forward with `FixedClock.advance(days)` instead of
  waiting three weeks.
- Library logic returns values and raises exceptions. It never prints.

## Getting started

```bash
pixi run projects          # list projects
pixi run start p02         # copies starter/ to work/p02_library_system/
pixi run grade p02         # runs the tests against your work/ copy
pixi run grade p02 -- -k isbn   # run one milestone's tests (arguments after -- go to pytest)
```

Edit the files in `work/p02_library_system/library/`. Every function has its signature, a docstring, and a
`TODO` that tells you what to do. Replace each `raise NotImplementedError`.

Type-check your work with:

```bash
pixi run mypy --strict work/p02_library_system/library
```

## Milestones

| # | Area | Modules | Tests |
|---|---|---|---|
| 1 | ISBN validation and records | `isbn.py`, `models.py`, `clock.py` | `test_library_isbn.py`, `test_library_models.py` |
| 2 | Catalog, members, loans, fines | `library.py` | `test_library_loans.py` |
| 3 | Holds and notifications | `library.py`, `notify.py` | `test_library_holds.py` |
| 4 | Keyword search | `search.py` | `test_library_search.py` |
| 5 | JSON persistence | `storage.py` | `test_library_storage.py` |

## Stretch goals

- A `main()` CLI with `argparse` subcommands (`add`, `lend`, `return`, `search`, `overdue`) that loads and saves
  `library.json`.
- An `EmailNotifier` that formats messages with `string.Template` and writes them to an outbox directory.
- Ranked search: score books by how many query words match and allow prefix matches (`tolk` finds Tolkien).
- Renewals: extend a loan once unless someone is waiting for the title.
- Property-based tests with Hypothesis: every ISBN-10 converted to ISBN-13 validates.
