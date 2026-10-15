"""Offline evaluation: per-user hold-out split, rating error, and ranking metrics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from recommender.base import Recommender
from recommender.data import RatingMatrix


def train_test_split_by_user(
    data: RatingMatrix, test_fraction: float = 0.2, seed: int = 0, min_ratings: int = 5
) -> tuple[RatingMatrix, np.ndarray]:
    """Hold out a fraction of each user's ratings for testing.

    Users with fewer than ``min_ratings`` ratings keep everything in train. Every other user keeps at
    least one training rating and gives at least one test rating, so no user is cold at test time.

    Args:
        data: All ratings.
        test_fraction: Fraction of each eligible user's ratings to hold out, in ``(0, 1)``.
        seed: Random seed for the hold-out choice.
        min_ratings: Minimum ratings a user needs to contribute test ratings.

    Returns:
        ``(train, test)`` where ``train`` shares ``data``'s id mappings and ``test`` is an array of
        ``(user_index, item_index, rating)`` rows.

    Raises:
        ValueError: If ``test_fraction`` is not in ``(0, 1)``.
    """
    # TODO: For each user with >= max(2, min_ratings) ratings, hold out
    # TODO: min(n - 1, max(1, round(test_fraction * n))) ratings chosen with the seeded rng.
    # TODO: Rebuild a CSR train matrix with the same shape; return it via data.with_matrix(...).
    raise NotImplementedError


def top_k(scores: np.ndarray, k: int, exclude: Iterable[int] = ()) -> list[int]:
    """Return the indices of the ``k`` highest scores, best first, skipping ``exclude``.

    Ties are broken by the lower index so results are deterministic.

    Args:
        scores: One score per item.
        k: How many to return (``>= 1``).
        exclude: Item indices that must not appear.

    Returns:
        Up to ``k`` item indices.

    Raises:
        ValueError: If ``k < 1``.
    """
    # TODO: Set excluded scores to -inf, argsort descending with kind='stable', drop -inf, take k.
    raise NotImplementedError


def precision_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """Fraction of the first ``k`` recommendations that are relevant (divides by ``k``)."""
    # TODO: hits in recommended[:k] / k
    raise NotImplementedError


def recall_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """Fraction of the relevant items found in the first ``k`` recommendations (``0.0`` if none are relevant)."""
    # TODO: hits in recommended[:k] / len(relevant); 0.0 if nothing is relevant
    raise NotImplementedError


def coverage(recommendations: Iterable[Sequence[int]], n_items: int) -> float:
    """Fraction of the catalogue that appears in at least one recommendation list."""
    # TODO: Distinct recommended items / n_items.
    raise NotImplementedError


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Metrics for one model.

    Attributes:
        rmse: Root mean squared error on the test ratings.
        precision: Mean precision@k over users with at least one relevant test item.
        recall: Mean recall@k over the same users.
        coverage: Catalogue coverage of all users' top-k lists.
    """

    rmse: float
    precision: float
    recall: float
    coverage: float


def evaluate(model: Recommender, test: np.ndarray, k: int = 10, threshold: float = 4.0) -> EvaluationResult:
    """Evaluate a fitted model on held-out ratings.

    A test item is relevant when its rating is ``>= threshold``. Each user's ranking excludes the items
    they rated in the training matrix.

    Args:
        model: A model already fitted on the training matrix.
        test: ``(user, item, rating)`` rows from :func:`train_test_split_by_user`.
        k: Cut-off for the ranking metrics.
        threshold: Minimum rating that counts as relevant.

    Returns:
        The metrics.

    Raises:
        ValueError: If ``test`` is empty.
    """
    # TODO: RMSE via model.predict_many(test). For each test user: relevant = test items rated >= threshold,
    # TODO: ranked = top_k(score_items(u), k, exclude=items seen in model.train). Average precision/recall
    # TODO: over users with relevant items; coverage over all users' lists.
    raise NotImplementedError


def compare_models(
    models: Mapping[str, Recommender], train: RatingMatrix, test: np.ndarray, k: int = 10, threshold: float = 4.0
) -> dict[str, EvaluationResult]:
    """Fit each model on ``train`` and evaluate it on ``test``.

    Args:
        models: Name to unfitted model.
        train: Training matrix.
        test: Held-out rows.
        k: Ranking cut-off.
        threshold: Relevance threshold.

    Returns:
        Name to metrics, in the input order.
    """
    # TODO: {name: evaluate(model.fit(train), test, k, threshold)}
    raise NotImplementedError


def format_table(results: Mapping[str, EvaluationResult], k: int = 10) -> str:
    """Render results as a Markdown table sorted by RMSE (best first).

    Args:
        results: Name to metrics.
        k: The cut-off used, for the column headers.

    Returns:
        The table text.
    """
    # TODO: Markdown header, separator, then one row per model sorted by RMSE.
    raise NotImplementedError
