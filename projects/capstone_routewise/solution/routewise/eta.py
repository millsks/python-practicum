"""Synthetic delivery history, an ETA model with scikit-learn, evaluation against a naive baseline, and simulation."""

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from routewise.routing import Delivery, Instance, Plan, schedule

WEATHER = ("clear", "rain", "snow")
FEATURES = ("planned_minutes", "service_minutes", "demand", "hour", "weekday", "weather", "van")
CATEGORICAL = (4, 5, 6)
NUMERIC = (0, 1, 2, 3)

ModelKind = Literal["gbr", "ridge"]


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    """One historical leg: drive to a customer and unload.

    Attributes:
        planned_minutes: Travel minutes the planner expected for the leg.
        service_minutes: Planned unloading minutes.
        demand: Crates delivered.
        hour: Hour of day the leg started (8 to 17).
        weekday: Day of week, Monday = 0.
        weather: One of :data:`WEATHER`.
        van: Van index (0 to 3).
        actual_minutes: Observed minutes for driving plus unloading (the target).
    """

    planned_minutes: float
    service_minutes: float
    demand: int
    hour: int
    weekday: int
    weather: str
    van: int
    actual_minutes: float

    @property
    def naive_estimate(self) -> float:
        """The planner's own estimate: planned travel plus planned service."""
        return self.planned_minutes + self.service_minutes


@dataclass(frozen=True, slots=True)
class EtaMetrics:
    """Error metrics of a model and of the naive baseline on the same records (minutes)."""

    mae: float
    rmse: float
    baseline_mae: float
    baseline_rmse: float
    n: int

    @property
    def improvement(self) -> float:
        """Fraction by which the model's MAE beats the baseline's (0.25 means 25% lower error)."""
        return 1.0 - self.mae / self.baseline_mae if self.baseline_mae else 0.0


def _true_minutes(
    planned: float, service: float, demand: int, hour: int, weekday: int, weather: str, van: int
) -> float:
    rush = 1.4 if hour in (8, 16, 17) else 1.0
    weekend = 0.85 if weekday >= 5 else 1.0
    weather_factor = {"clear": 1.0, "rain": 1.2, "snow": 1.55}[weather]
    slow_van = 2.5 if van == 3 else 0.0
    return planned * rush * weekend * weather_factor + service + 0.6 * demand + slow_van


def generate_history(n_records: int, seed: int = 0) -> list[DeliveryRecord]:
    """Generate reproducible past deliveries with realistic structure.

    Actual minutes depend on rush hour, weekends, weather, load size, and one slow van, plus Gaussian noise, so a
    model that learns these effects beats the planner's naive estimate.

    Args:
        n_records: Number of records.
        seed: Random seed.

    Returns:
        The records.
    """
    rng = random.Random(seed)
    records: list[DeliveryRecord] = []
    for _ in range(n_records):
        planned = round(rng.uniform(2.0, 30.0), 2)
        service = round(rng.uniform(2.0, 8.0), 1)
        demand = rng.randint(1, 8)
        hour = rng.randint(8, 17)
        weekday = rng.randrange(7)
        weather = rng.choices(WEATHER, weights=(0.7, 0.2, 0.1))[0]
        van = rng.randrange(4)
        actual = _true_minutes(planned, service, demand, hour, weekday, weather, van) + rng.gauss(0.0, 1.5)
        records.append(
            DeliveryRecord(planned, service, demand, hour, weekday, weather, van, round(max(1.0, actual), 2))
        )
    return records


def to_features(records: Sequence[DeliveryRecord]) -> np.ndarray:
    """Encode records as a float matrix with columns in :data:`FEATURES` order (weather as its index)."""
    return np.array(
        [
            [r.planned_minutes, r.service_minutes, r.demand, r.hour, r.weekday, WEATHER.index(r.weather), r.van]
            for r in records
        ],
        dtype=float,
    ).reshape(len(records), len(FEATURES))


def to_target(records: Sequence[DeliveryRecord]) -> np.ndarray:
    """Return the actual minutes of each record."""
    return np.array([r.actual_minutes for r in records], dtype=float)


def build_model(kind: ModelKind = "gbr", seed: int = 0) -> Pipeline:
    """Create an unfitted feature pipeline plus regressor.

    Categorical columns (weekday, weather, van) are one-hot encoded; numeric columns pass through (and are scaled
    for Ridge).

    Args:
        kind: ``"gbr"`` for gradient boosting or ``"ridge"`` for ridge regression.
        seed: Random state for gradient boosting.

    Returns:
        The pipeline.

    Raises:
        ValueError: If ``kind`` is unknown.
    """
    numeric: StandardScaler | str = StandardScaler() if kind == "ridge" else "passthrough"
    features = ColumnTransformer(
        [
            ("categorical", OneHotEncoder(handle_unknown="ignore"), list(CATEGORICAL)),
            ("numeric", numeric, list(NUMERIC)),
        ]
    )
    if kind == "gbr":
        regressor: GradientBoostingRegressor | Ridge = GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.1, random_state=seed
        )
    elif kind == "ridge":
        regressor = Ridge(alpha=1.0)
    else:
        raise ValueError(f"unknown model kind {kind!r}")
    return Pipeline([("features", features), ("model", regressor)])


def train_eta_model(records: Sequence[DeliveryRecord], kind: ModelKind = "gbr", seed: int = 0) -> Pipeline:
    """Fit an ETA model on historical records.

    Args:
        records: Training records.
        kind: Model family.
        seed: Random state.

    Returns:
        The fitted pipeline.

    Raises:
        ValueError: If ``records`` is empty.
    """
    if not records:
        raise ValueError("cannot train on zero records")
    model = build_model(kind, seed)
    model.fit(to_features(records), to_target(records))
    return model


def predict_minutes(model: Pipeline, records: Sequence[DeliveryRecord]) -> np.ndarray:
    """Predict actual minutes for each record (the ``actual_minutes`` field is ignored)."""
    return np.asarray(model.predict(to_features(records)), dtype=float)


def evaluate(model: Pipeline, records: Sequence[DeliveryRecord]) -> EtaMetrics:
    """Compare a fitted model with the naive baseline on held-out records.

    Raises:
        ValueError: If ``records`` is empty.
    """
    if not records:
        raise ValueError("cannot evaluate on zero records")
    truth = to_target(records)
    model_error = predict_minutes(model, records) - truth
    baseline_error = np.array([r.naive_estimate for r in records]) - truth
    return EtaMetrics(
        mae=float(np.mean(np.abs(model_error))),
        rmse=float(np.sqrt(np.mean(model_error**2))),
        baseline_mae=float(np.mean(np.abs(baseline_error))),
        baseline_rmse=float(np.sqrt(np.mean(baseline_error**2))),
        n=len(records),
    )


def split(
    records: Sequence[DeliveryRecord], test_fraction: float = 0.25, seed: int = 0
) -> tuple[list[DeliveryRecord], list[DeliveryRecord]]:
    """Shuffle deterministically and split into ``(train, test)``.

    Raises:
        ValueError: If ``test_fraction`` is not strictly between 0 and 1 or a side would be empty.
    """
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1")
    order = list(range(len(records)))
    random.Random(seed).shuffle(order)
    cut = round(len(records) * test_fraction)
    if cut == 0 or cut == len(records):
        raise ValueError("not enough records to split")
    test = [records[i] for i in order[:cut]]
    train = [records[i] for i in order[cut:]]
    return train, test


def train_and_evaluate(
    records: Sequence[DeliveryRecord], kind: ModelKind = "gbr", test_fraction: float = 0.25, seed: int = 0
) -> tuple[Pipeline, EtaMetrics]:
    """Split, train, and evaluate in one call.

    Returns:
        The fitted model and its test-set metrics.
    """
    train, test = split(records, test_fraction, seed)
    model = train_eta_model(train, kind, seed)
    return model, evaluate(model, test)


def simulate_deliveries(plan: Plan, inst: Instance, seed: int = 0, noise: float = 0.15) -> list[Delivery]:
    """Simulate what actually happens when the vans drive a plan.

    Each leg's travel time is multiplied by a log-normal factor (slightly slower than planned on average); vans
    still wait for windows to open.

    Args:
        plan: Plan to execute.
        inst: Problem instance.
        seed: Random seed.
        noise: Standard deviation of the log travel-time factor.

    Returns:
        One delivery per served customer, in plan order.
    """
    rng = random.Random(seed)
    deliveries: list[Delivery] = []
    for van, route in enumerate(plan.routes):
        planned = schedule(route, inst).visits
        clock, here = 0.0, 0
        for visit in planned:
            customer = inst.customers[visit.customer]
            leg = inst.time(here, visit.customer) * math.exp(rng.gauss(0.05, noise))
            arrival = clock + leg
            deliveries.append(Delivery(visit.customer, van, visit.arrival, arrival, customer.due))
            clock = max(arrival, customer.ready) + customer.service
            here = visit.customer
    return deliveries
