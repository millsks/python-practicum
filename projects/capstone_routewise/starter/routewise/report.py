"""Key performance indicators for a plan and a text or Markdown report."""

import math  # noqa: F401
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from routewise.routing import Delivery, Instance, Plan, schedule  # noqa: F401

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
    # TODO: schedule every non-empty route; sum travel, end times, waits; utilization = mean load / capacity.
    raise NotImplementedError


def _kpi_rows(kpis: Kpis) -> list[tuple[str, str]]:
    # TODO: implement this function.
    raise NotImplementedError


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
    # TODO: build (metric, value) rows once; format them as a Markdown table or aligned text.
    raise NotImplementedError
