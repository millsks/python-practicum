# python-practicum

An interactive, novice-to-pro curriculum for Python 3.14 (with Python 3.15 previews): the language, data structures,
algorithms, data science, machine learning, and data engineering. Everything is managed with Pixi.

[![CI](https://github.com/millsks/python-practicum/actions/workflows/ci.yml/badge.svg)](https://github.com/millsks/python-practicum/actions/workflows/ci.yml)
![coverage](https://img.shields.io/badge/coverage-%E2%89%A590%25-brightgreen)
![python](https://img.shields.io/badge/python-3.14-blue)
![pixi](https://img.shields.io/badge/managed%20by-pixi-orange)

**Take the course online:** https://millsks.github.io/python-practicum/

## What's inside

- **64 interactive lesson modules** in 10 parts, published as static HTML in [`docs/`](docs/):
  0 Orientation · 1 Foundations · 2 Intermediate Python · 3 Data Structures · 4 Algorithms · 5 Advanced Python ·
  6 Professional Python · 7 Scientific Computing & Data Science · 8 Machine Learning · 9 Data Engineering · 10 Capstone
- **Real Python 3.14 in the browser** (Pyodide). Lessons include editable runnable cells, predict-the-output
  challenges, a step-through execution tracer, and animated visualizers for data structures and algorithms.
- **Graded exercises, end-of-module quizzes, flashcards, and mini-projects** in every module. Progress, notes, and
  scores are saved in your browser.
- **Nine graded projects plus a capstone** in [`projects/`](projects/): starter code, a test suite, and a
  reference solution for each.
- **Reference pages**: what's new in 3.14, a 3.15 preview, plus Pixi, Python, and complexity cheat sheets and a glossary.

## Installation

Install [Pixi](https://pixi.sh), then:

```sh
git clone https://github.com/millsks/python-practicum.git
cd python-practicum
pixi install          # Python 3.14 + numpy, scipy, pandas, scikit-learn, matplotlib, polars, duckdb, ...
pixi run bootstrap    # pre-commit hooks (only needed if you contribute)
```

## Quick start

```sh
pixi run serve        # opens the course at http://127.0.0.1:8000/
```

Start with **Module 00: Setup**. When a part ends, build its project:

```sh
pixi run projects     # list projects and whether you've started them
pixi run start p01    # copy the starter code into work/p01_budget_ledger/
pixi run grade p01    # run the project's tests against your code in work/
```

Your code lives in `work/`. The starters in `projects/*/starter/` stay untouched, so you can restart a project with
`pixi run practicum start p01 --force`. Each project also ships a `solution/` directory; try to finish without it.

## Development

```sh
pixi run test               # unit tests (fast)
pixi run test-integration   # integration tests: every exercise solution and project solution is verified
pixi run check-site         # validate links, anchors, quizzes, exercises, and visualizers in docs/
pixi run practicum check-exercises docs/modules/m05-functions.html
pixi run bundle             # build the single-file edition: dist/python-practicum.html (one page, every module)
pixi run ci                 # pre-commit, build, mypy, ruff, and tests with a coverage gate (>= 90%)
```

Lesson authors should read [`docs/AUTHORING.md`](docs/AUTHORING.md). The component gallery is at
`/authoring/components.html` when the site is served.

## License

[MIT](LICENSE)
