"""Milestone 6: synthetic delivery history, the ETA model, evaluation against a baseline, and simulation."""

import pytest
from routewise.assign import plan_routes
from routewise.data import generate_city
from routewise.eta import (
    FEATURES,
    WEATHER,
    evaluate,
    generate_history,
    simulate_deliveries,
    split,
    to_features,
    train_and_evaluate,
    train_eta_model,
)
from routewise.routing import Instance


@pytest.fixture(scope="module")
def history():
    return generate_history(1600, seed=0)


def test_history_is_deterministic_and_valid(history):
    assert generate_history(50, seed=4) == generate_history(50, seed=4), "same seed, same history"
    assert len(history) == 1600
    for r in history[:200]:
        assert r.weather in WEATHER and 8 <= r.hour <= 17 and 0 <= r.weekday <= 6
        assert r.actual_minutes >= 1.0, "actual minutes are clipped at one minute"


def test_feature_matrix_shape(history):
    x = to_features(history[:10])
    assert x.shape == (10, len(FEATURES)), "one column per feature"
    assert to_features([]).shape == (0, len(FEATURES))


def test_split_is_deterministic_and_disjoint(history):
    train, test = split(history, 0.25, seed=1)
    assert len(test) == 400 and len(train) == 1200
    assert split(history, 0.25, seed=1) == (train, test), "the split must be reproducible"
    with pytest.raises(ValueError):
        split(history, 1.5)


@pytest.mark.parametrize("kind", ["gbr", "ridge"])
def test_model_beats_naive_baseline(history, kind):
    _, metrics = train_and_evaluate(history, kind=kind, seed=0)
    assert metrics.n == 400
    assert metrics.mae < metrics.baseline_mae, f"{kind} must have lower MAE than the naive estimate"
    assert metrics.rmse >= metrics.mae, "RMSE is never smaller than MAE"


def test_gradient_boosting_is_clearly_better(history):
    _, metrics = train_and_evaluate(history, kind="gbr", seed=0)
    assert metrics.improvement > 0.5, "gradient boosting should cut the baseline's error by more than half"


def test_training_is_reproducible(history):
    train, test = split(history, seed=2)
    first = evaluate(train_eta_model(train, seed=3), test)
    second = evaluate(train_eta_model(train, seed=3), test)
    assert first == second, "the same data and seed must give identical metrics"


def test_empty_inputs_rejected():
    with pytest.raises(ValueError):
        train_eta_model([])
    with pytest.raises(ValueError):
        train_and_evaluate(generate_history(1, seed=0))


def test_simulated_deliveries_cover_plan():
    inst = Instance.from_city(generate_city(30, seed=6), capacity=50)
    plan = plan_routes(inst)
    deliveries = simulate_deliveries(plan, inst, seed=1)
    assert sorted(d.customer for d in deliveries) == sorted(inst.customers), "one delivery per customer"
    assert deliveries == simulate_deliveries(plan, inst, seed=1), "simulation is deterministic per seed"
    assert deliveries != simulate_deliveries(plan, inst, seed=2), "a different seed changes the day"
    assert {d.van for d in deliveries} == set(range(len(plan.routes)))
