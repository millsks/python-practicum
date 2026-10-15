"""Milestone 7: SQLite persistence of plans and deliveries."""

import pytest
from routewise.routing import Delivery, Plan, Route
from routewise.store import PlanNotFoundError, Store

PLAN = Plan((Route((3, 1)), Route((2,)), Route((5, 4, 6))), "savings")


def test_plan_round_trip(tmp_path):
    with Store(tmp_path / "rw.db") as store:
        plan_id = store.save_plan(PLAN, label="demo", capacity=40)
        assert store.load_plan(plan_id) == PLAN, "a loaded plan must equal the saved one, order included"


def test_ids_increase_and_list_plans(tmp_path):
    with Store(tmp_path / "rw.db") as store:
        first = store.save_plan(PLAN, label="a", capacity=40, created_at="2026-01-01T00:00:00+00:00")
        second = store.save_plan(Plan((Route((1,)),), "nearest"), label="b", capacity=20)
        assert second > first
        assert store.latest_plan_id() == second
        summaries = store.list_plans()
    assert [s.label for s in summaries] == ["a", "b"]
    assert (summaries[0].n_routes, summaries[0].n_stops, summaries[0].method) == (3, 6, "savings")
    assert summaries[0].created_at == "2026-01-01T00:00:00+00:00" and summaries[0].capacity == 40


def test_data_survives_reopening(tmp_path):
    path = tmp_path / "rw.db"
    with Store(path) as store:
        plan_id = store.save_plan(PLAN)
    with Store(path) as store:
        assert store.load_plan(plan_id) == PLAN, "data must persist on disk"


def test_missing_plan_raises(tmp_path):
    with Store(tmp_path / "rw.db") as store:
        assert store.latest_plan_id() is None
        with pytest.raises(PlanNotFoundError):
            store.load_plan(7)
        with pytest.raises(PlanNotFoundError):
            store.save_deliveries(7, [])


def test_deliveries_round_trip_and_replace():
    with Store(":memory:") as store:
        plan_id = store.save_plan(PLAN)
        deliveries = [Delivery(3, 0, 10.0, 12.5, 30.0), Delivery(1, 0, 25.0, 40.0, 35.0)]
        assert store.save_deliveries(plan_id, deliveries) == 2
        assert store.load_deliveries(plan_id) == deliveries
        store.save_deliveries(plan_id, [Delivery(1, 0, 25.0, 30.0, 35.0)])
        loaded = store.load_deliveries(plan_id)
    assert len(loaded) == 2 and loaded[1].actual_arrival == 30.0, "re-recording a customer replaces the row"
    assert loaded[1].on_time and loaded[1].delay == 5.0
