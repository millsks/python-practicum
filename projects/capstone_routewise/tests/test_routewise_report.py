"""Milestone 8: KPIs and the daily report."""

import pytest
from routewise.data import Customer
from routewise.graph import DistanceMatrix, RoadGraph
from routewise.report import compute_kpis, render_report
from routewise.routing import Delivery, Instance, Plan, Route


@pytest.fixture
def line():
    coords = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (2.0, 0.0)}
    graph = RoadGraph.from_edges(coords, [(0, 1, 10.0), (1, 2, 10.0)])
    customers = {
        1: Customer(1, 1, 3, ready=30.0, due=60.0, service=5.0),
        2: Customer(2, 2, 4, ready=0.0, due=50.0, service=5.0),
    }
    return Instance(0, customers, DistanceMatrix(graph, [0, 1, 2]), 10, 600, coords)


def test_kpis_for_single_route(line):
    kpis = compute_kpis(Plan((Route((1, 2)),), "manual"), line)
    assert (kpis.n_customers, kpis.n_routes) == (2, 1)
    assert kpis.total_travel_minutes == 40.0 and kpis.total_duration_minutes == 70.0
    assert kpis.total_wait_minutes == 20.0 and kpis.planned_on_time_pct == 100.0
    assert kpis.utilization == pytest.approx(0.7) and kpis.max_load == 7
    assert kpis.actual_on_time_pct is None and kpis.mean_delay_minutes is None


def test_kpis_two_vans_and_lateness(line):
    kpis = compute_kpis(Plan((Route((1,)), Route((2,)))), line)
    assert kpis.n_routes == 2 and kpis.utilization == pytest.approx(7 / 20), "mean load / capacity"
    deliveries = [Delivery(1, 0, 10.0, 70.0, 60.0), Delivery(2, 1, 20.0, 22.0, 50.0)]
    with_actuals = compute_kpis(Plan((Route((1,)), Route((2,)))), line, deliveries)
    assert with_actuals.actual_on_time_pct == 50.0, "one of two deliveries arrived after its window"
    assert with_actuals.mean_delay_minutes == pytest.approx(31.0)


def test_empty_plan_kpis(line):
    kpis = compute_kpis(Plan(()), line)
    assert kpis.n_customers == 0 and kpis.utilization == 0.0 and kpis.planned_on_time_pct == 100.0


def test_markdown_report(line):
    text = render_report(Plan((Route((1, 2)),), "savings"), line)
    assert text.startswith("# RouteWise daily report (savings)"), "markdown report starts with an H1"
    assert "| Metric | Value |" in text and "| Vans used | 1 |" in text
    assert "## Routes" in text and "| 0 | 2 | 7 | 40.0 | 70.0 |" in text


def test_text_report_and_actuals(line):
    deliveries = [Delivery(1, 0, 10.0, 12.0, 60.0), Delivery(2, 0, 45.0, 47.0, 50.0)]
    text = render_report(Plan((Route((1, 2)),)), line, deliveries, fmt="text")
    assert "|" not in text, "plain text has no table pipes"
    assert "Actual on-time" in text and "100.0%" in text and "+2.0" in text
    with pytest.raises(ValueError):
        render_report(Plan(()), line, fmt="html")
