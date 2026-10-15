"""Synthetic delivery history, an ETA model with scikit-learn, evaluation against a naive baseline, and simulation."""

import math  # noqa: F401
import random  # noqa: F401
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from sklearn.compose import ColumnTransformer  # noqa: F401
from sklearn.ensemble import GradientBoostingRegressor  # noqa: F401
from sklearn.linear_model import Ridge  # noqa: F401
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: F401

from routewise.routing import Delivery, Instance, Plan, schedule  # noqa: F401

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
    # TODO: implement this function.
    raise NotImplementedError


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
    # TODO: random.Random(seed); actual = f(planned, rush hour, weekend, weather, demand, van) + noise.
    raise NotImplementedError


def to_features(records: Sequence[DeliveryRecord]) -> np.ndarray:
    """Encode records as a float matrix with columns in :data:`FEATURES` order (weather as its index)."""
    # TODO: implement this function.
    raise NotImplementedError


def to_target(records: Sequence[DeliveryRecord]) -> np.ndarray:
    """Return the actual minutes of each record."""
    # TODO: implement this function.
    raise NotImplementedError


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
    # TODO: ColumnTransformer(OneHotEncoder on categorical columns, numeric passthrough/scaled) + regressor.
    raise NotImplementedError


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
    # TODO: implement this function.
    raise NotImplementedError


def predict_minutes(model: Pipeline, records: Sequence[DeliveryRecord]) -> np.ndarray:
    """Predict actual minutes for each record (the ``actual_minutes`` field is ignored)."""
    # TODO: implement this function.
    raise NotImplementedError


def evaluate(model: Pipeline, records: Sequence[DeliveryRecord]) -> EtaMetrics:
    """Compare a fitted model with the naive baseline on held-out records.

    Raises:
        ValueError: If ``records`` is empty.
    """
    # TODO: MAE and RMSE for the model and for the naive estimate (planned + service) on the same records.
    raise NotImplementedError


def split(
    records: Sequence[DeliveryRecord], test_fraction: float = 0.25, seed: int = 0
) -> tuple[list[DeliveryRecord], list[DeliveryRecord]]:
    """Shuffle deterministically and split into ``(train, test)``.

    Raises:
        ValueError: If ``test_fraction`` is not strictly between 0 and 1 or a side would be empty.
    """
    # TODO: implement this function.
    raise NotImplementedError


def train_and_evaluate(
    records: Sequence[DeliveryRecord], kind: ModelKind = "gbr", test_fraction: float = 0.25, seed: int = 0
) -> tuple[Pipeline, EtaMetrics]:
    """Split, train, and evaluate in one call.

    Returns:
        The fitted model and its test-set metrics.
    """
    # TODO: implement this function.
    raise NotImplementedError


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
    # TODO: multiply each planned leg by exp(gauss(0.05, noise)); vans still wait for windows.
    raise NotImplementedError
