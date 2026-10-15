# Capstone: RouteWise Delivery Planner

A local bakery cooperative delivers bread to 30 to 200 cafes, shops, and households every morning with a handful of
vans. Today a dispatcher plans routes by hand on a whiteboard. Vans run out of space, cafes complain about late
croissants, and nobody knows how long a stop really takes. You will build **RouteWise**: a tested, typed Python package
that plans daily routes under van capacity and delivery time windows, predicts delivery durations from history, stores
plans and outcomes in SQLite, and reports performance.

The full brief, with architecture and ER diagrams, module links, hints, and the rubric, is on the course site:
`docs/projects/capstone.html`.

## How to start and grade

```bash
pixi run start capstone        # copies starter/ into work/capstone_routewise/
pixi run grade capstone        # runs every test in tests/ against your work/ copy
pixi run grade capstone -- -k graph -x   # one area, stop at the first failure
```

Edit the files in `work/capstone_routewise/routewise/`. Every public function already has its signature, type hints,
docstring, and a `TODO` hint; replace each `raise NotImplementedError` with a real implementation.

Run the CLI from your working copy:

```bash
cd work/capstone_routewise
pixi run python -m routewise generate --customers 60 --seed 7 --out city
pixi run python -m routewise plan --city city --db routewise.db --method savings --simulate
pixi run python -m routewise report --city city --db routewise.db --format markdown
```

## Constraints

- Standard library, NumPy, and scikit-learn only. No network access. Everything is deterministic given a seed.
- Full type hints, Google-style docstrings, ruff-clean (`pixi run ruff check work/capstone_routewise`).
- Library code returns values; only `cli.main` prints.

## Package layout

| Module | Responsibility |
|---|---|
| `data` | `Node`, `Edge`, `Customer`, `City`; `generate_city(n, seed)`; `save_city` / `load_city` (CSV) |
| `graph` | `RoadGraph` adjacency list; `dijkstra`, `shortest_path`, `a_star`, `reconstruct_path`; cached `DistanceMatrix` |
| `routing` | `Instance`, `Route`, `Plan`, `Visit`, `Schedule`, `Delivery`; `schedule`, `check_plan`; `nearest_neighbor`, `clarke_wright`, `two_opt`, `held_karp` |
| `assign` | `polar_angle`, `sweep_clusters`, `sweep`, `plan_routes(inst, method, improve=True)` |
| `eta` | `generate_history`, `build_model`, `train_eta_model`, `evaluate`, `train_and_evaluate`, `simulate_deliveries` |
| `store` | `Store` (SQLite): `save_plan`, `load_plan`, `list_plans`, `save_deliveries`, `load_deliveries` |
| `report` | `Kpis`, `compute_kpis`, `render_report(fmt="markdown" or "text")` |
| `cli` | `routewise generate`, `plan`, `report` |

## Milestones (tests file in brackets)

1. City data and the generator (`test_routewise_data.py`)
2. Road graph, Dijkstra, A*, and the distance matrix (`test_routewise_graph.py`)
3. Route model and feasibility (`test_routewise_routing.py`, schedule and check tests)
4. Exact Held-Karp baseline (`test_routewise_routing.py`, held_karp tests)
5. Construction heuristics and 2-opt (`test_routewise_routing.py`)
6. Assigning customers to vans: the sweep algorithm (`test_routewise_assign.py`)
7. The ETA model (`test_routewise_eta.py`)
8. Persistence (`test_routewise_store.py`)
9. KPIs and reporting (`test_routewise_report.py`)
10. The CLI and the final polish (`test_routewise_cli.py`)

## Stretch goals

- A FastAPI service (`pixi add fastapi uvicorn`) exposing `POST /plans` and `GET /plans/{id}/report`.
- A map of the routes with matplotlib (one colour per van).
- Real road data via `osmnx` (`pixi add osmnx`) in a separate, network-enabled Pixi feature.
- Parallel optimization on the free-threaded 3.14 build: improve routes concurrently with a thread pool.
- Python 3.15 preview: `lazy import sklearn` in the CLI so `routewise generate` starts faster.
