"""Offline evaluation: per-user hold-out split, rating error, and ranking metrics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix

from recommender.base import Recommender
from recommender.data import RatingMatrix
from recommender.mf import rmse


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
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be in (0, 1)")
    rng = np.random.default_rng(seed)
    train_rows: list[np.ndarray] = []
    test_rows: list[np.ndarray] = []
    for user in range(data.n_users):
        items, ratings = data.user_ratings(user)
        triples = np.column_stack([np.full(len(items), user), items, ratings]).astype(float)
        if len(items) < max(2, min_ratings):
            train_rows.append(triples)
            continue
        n_test = min(len(items) - 1, max(1, round(test_fraction * len(items))))
        held = rng.choice(len(items), size=n_test, replace=False)
        mask = np.zeros(len(items), dtype=bool)
        mask[held] = True
        test_rows.append(triples[mask])
        train_rows.append(triples[~mask])
    train = np.vstack(train_rows) if train_rows else np.zeros((0, 3))
    test = np.vstack(test_rows) if test_rows else np.zeros((0, 3))
    matrix = csr_matrix(
        (train[:, 2], (train[:, 0].astype(int), train[:, 1].astype(int))), shape=(data.n_users, data.n_items)
    )
    matrix.sort_indices()
    return data.with_matrix(matrix), test


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
    if k < 1:
        raise ValueError("k must be >= 1")
    masked = np.asarray(scores, dtype=float).copy()
    excluded = list(exclude)
    if excluded:
        masked[excluded] = -np.inf
    order = np.argsort(-masked, kind="stable")
    return [int(i) for i in order if np.isfinite(masked[i])][:k]


def precision_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """Fraction of the first ``k`` recommendations that are relevant (divides by ``k``)."""
    if k < 1:
        raise ValueError("k must be >= 1")
    return sum(1 for item in recommended[:k] if item in relevant) / k


def recall_at_k(recommended: Sequence[int], relevant: set[int], k: int) -> float:
    """Fraction of the relevant items found in the first ``k`` recommendations (``0.0`` if none are relevant)."""
    if k < 1:
        raise ValueError("k must be >= 1")
    if not relevant:
        return 0.0
    return sum(1 for item in recommended[:k] if item in relevant) / len(relevant)


def coverage(recommendations: Iterable[Sequence[int]], n_items: int) -> float:
    """Fraction of the catalogue that appears in at least one recommendation list."""
    if n_items < 1:
        raise ValueError("n_items must be >= 1")
    seen: set[int] = set()
    for items in recommendations:
        seen.update(items)
    return len(seen) / n_items


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
    if len(test) == 0:
        raise ValueError("test set is empty")
    train = model.train
    error = rmse(test[:, 2], model.predict_many(test))
    precisions: list[float] = []
    recalls: list[float] = []
    lists: list[list[int]] = []
    users = test[:, 0].astype(int)
    for user in np.unique(users):
        rows = test[users == user]
        relevant = {int(i) for i, r in zip(rows[:, 1], rows[:, 2], strict=True) if r >= threshold}
        seen, _ = train.user_ratings(int(user))
        ranked = top_k(model.score_items(int(user)), k, exclude=seen)
        lists.append(ranked)
        if relevant:
            precisions.append(precision_at_k(ranked, relevant, k))
            recalls.append(recall_at_k(ranked, relevant, k))
    return EvaluationResult(
        rmse=error,
        precision=float(np.mean(precisions)) if precisions else 0.0,
        recall=float(np.mean(recalls)) if recalls else 0.0,
        coverage=coverage(lists, train.n_items),
    )


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
    return {name: evaluate(model.fit(train), test, k, threshold) for name, model in models.items()}


def format_table(results: Mapping[str, EvaluationResult], k: int = 10) -> str:
    """Render results as a Markdown table sorted by RMSE (best first).

    Args:
        results: Name to metrics.
        k: The cut-off used, for the column headers.

    Returns:
        The table text.
    """
    lines = [
        f"| model | RMSE | precision@{k} | recall@{k} | coverage |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, res in sorted(results.items(), key=lambda kv: kv[1].rmse):
        lines.append(f"| {name} | {res.rmse:.4f} | {res.precision:.4f} | {res.recall:.4f} | {res.coverage:.3f} |")
    return "\n".join(lines)
