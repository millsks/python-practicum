"""Key performance indicators for a plan and a text or Markdown report."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from routewise.routing import Delivery, Instance, Plan, schedule

ReportFormat = Literal["markdown", "text"]


@dataclass(frozen=True, slots=True)
class Kpis:
    """Headline numbers for one day's plan.

    Attributes:
        n_customers: Customers served.
        n_routes: Vans used.
        total_travel_minutes: Driving minutes over all routes.
        total_duration_minutes: Minutes from departure to return, summed over vans (driving, waiting, unloading).
        total_wait_minutes: Minutes spent waiting for windows to open.
        planned_on_time_pct: Percentage of planned visits that start inside their window.
        actual_on_time_pct: Percentage of actual deliveries that arrived in time, or ``None`` without deliveries.
        mean_delay_minutes: Mean actual-minus-planned arrival, or ``None`` without deliveries.
        utilization: Mean van load as a fraction of capacity (0 when capacity is unlimited).
        max_load: Heaviest van load.
        capacity: Van capacity.
    """

    n_customers: int
    n_routes: int
    total_travel_minutes: float
    total_duration_minutes: float
    total_wait_minutes: float
    planned_on_time_pct: float
    actual_on_time_pct: float | None
    mean_delay_minutes: float | None
    utilization: float
    max_load: float
    capacity: float


def compute_kpis(plan: Plan, inst: Instance, deliveries: Sequence[Delivery] | None = None) -> Kpis:
    """Compute KPIs from a plan's simulated schedule and, optionally, its actual deliveries.

    Args:
        plan: The plan.
        inst: Its instance.
        deliveries: Actual deliveries, if the day has happened.

    Returns:
        The KPIs.
    """
    schedules = [schedule(route, inst) for route in plan.routes if route.stops]
    visits = [v for s in schedules for v in s.visits]
    on_time = sum(v.start <= inst.customers[v.customer].due + 1e-9 for v in visits)
    loads = [s.load for s in schedules]
    utilization = sum(loads) / (len(loads) * inst.capacity) if loads and math.isfinite(inst.capacity) else 0.0
    actual_pct = mean_delay = None
    if deliveries:
        actual_pct = 100.0 * sum(d.on_time for d in deliveries) / len(deliveries)
        mean_delay = sum(d.delay for d in deliveries) / len(deliveries)
    return Kpis(
        n_customers=len(visits),
        n_routes=len(schedules),
        total_travel_minutes=sum(s.travel_minutes for s in schedules),
        total_duration_minutes=sum(s.end_time for s in schedules),
        total_wait_minutes=sum(s.total_wait for s in schedules),
        planned_on_time_pct=100.0 * on_time / len(visits) if visits else 100.0,
        actual_on_time_pct=actual_pct,
        mean_delay_minutes=mean_delay,
        utilization=utilization,
        max_load=max(loads, default=0.0),
        capacity=inst.capacity,
    )


def _kpi_rows(kpis: Kpis) -> list[tuple[str, str]]:
    rows = [
        ("Customers served", f"{kpis.n_customers}"),
        ("Vans used", f"{kpis.n_routes}"),
        ("Total travel (min)", f"{kpis.total_travel_minutes:.1f}"),
        ("Total van time (min)", f"{kpis.total_duration_minutes:.1f}"),
        ("Total waiting (min)", f"{kpis.total_wait_minutes:.1f}"),
        ("Planned on-time", f"{kpis.planned_on_time_pct:.1f}%"),
        ("Van utilization", f"{kpis.utilization:.1%}"),
        ("Heaviest load", f"{kpis.max_load:g} / {kpis.capacity:g}"),
    ]
    if kpis.actual_on_time_pct is not None and kpis.mean_delay_minutes is not None:
        rows.append(("Actual on-time", f"{kpis.actual_on_time_pct:.1f}%"))
        rows.append(("Mean delay (min)", f"{kpis.mean_delay_minutes:+.1f}"))
    return rows


def render_report(
    plan: Plan, inst: Instance, deliveries: Sequence[Delivery] | None = None, fmt: ReportFormat = "markdown"
) -> str:
    """Render a daily report with a KPI table and one line per route.

    Args:
        plan: The plan.
        inst: Its instance.
        deliveries: Actual deliveries, if any.
        fmt: ``"markdown"`` or ``"text"``.

    Returns:
        The report text, ending with a newline.

    Raises:
        ValueError: If ``fmt`` is unknown.
    """
    if fmt not in ("markdown", "text"):
        raise ValueError(f"unknown report format {fmt!r}")
    kpis = compute_kpis(plan, inst, deliveries)
    rows = _kpi_rows(kpis)
    routes = [(index, route, schedule(route, inst)) for index, route in enumerate(plan.routes) if route.stops]
    if fmt == "markdown":
        lines = [
            f"# RouteWise daily report ({plan.method or 'plan'})",
            "",
            "## KPIs",
            "",
            "| Metric | Value |",
            "|---|---|",
        ]
        lines += [f"| {name} | {value} |" for name, value in rows]
        lines += ["", "## Routes", "", "| Van | Stops | Load | Travel (min) | Back at (min) |", "|---|---|---|---|---|"]
        lines += [f"| {i} | {len(r)} | {s.load:g} | {s.travel_minutes:.1f} | {s.end_time:.1f} |" for i, r, s in routes]
    else:
        width = max(len(name) for name, _ in rows)
        lines = [f"RouteWise daily report ({plan.method or 'plan'})", ""]
        lines += [f"{name:<{width}}  {value}" for name, value in rows]
        lines += ["", "Routes:"]
        lines += [
            f"  van {i}: {len(r)} stops, load {s.load:g}, travel {s.travel_minutes:.1f} min, back at {s.end_time:.1f}"
            for i, r, s in routes
        ]
    return "\n".join(lines) + "\n"
