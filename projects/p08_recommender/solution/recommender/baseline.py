"""Popularity baseline ranked by a Bayesian (damped) average."""

from __future__ import annotations

from typing import Self

import numpy as np

from recommender.base import Recommender
from recommender.data import RatingMatrix


def bayesian_average(sums: np.ndarray, counts: np.ndarray, prior_mean: float, prior_weight: float) -> np.ndarray:
    """Shrink each item's mean rating toward a prior.

    ``(prior_weight * prior_mean + sum) / (prior_weight + count)``: an item with few ratings stays near
    the prior, an item with many ratings approaches its own mean.

    Args:
        sums: Sum of ratings per item.
        counts: Number of ratings per item.
        prior_mean: The value to shrink toward (usually the global mean).
        prior_weight: How many "virtual" prior ratings each item gets (``>= 0``).

    Returns:
        The damped mean per item; items with no ratings and zero weight get ``prior_mean``.

    Raises:
        ValueError: If ``prior_weight`` is negative.
    """
    if prior_weight < 0:
        raise ValueError("prior_weight must be >= 0")
    sums = np.asarray(sums, dtype=float)
    counts = np.asarray(counts, dtype=float)
    denom = prior_weight + counts
    safe = np.where(denom > 0, denom, 1.0)
    return np.where(denom > 0, (prior_weight * prior_mean + sums) / safe, prior_mean)


class PopularityRecommender(Recommender):
    """Recommend the same top items to everyone, ranked by Bayesian average rating.

    Args:
        prior_weight: Strength of the shrinkage toward the global mean.
    """

    def __init__(self, prior_weight: float = 5.0) -> None:
        """Store the prior weight."""
        self.prior_weight = prior_weight
        self.item_scores_: np.ndarray | None = None

    def fit(self, train: RatingMatrix) -> Self:
        """Compute the damped mean rating of every item.

        Args:
            train: Training ratings.

        Returns:
            ``self``.
        """
        sums = np.asarray(train.matrix.sum(axis=0)).ravel()
        counts = train.counts_per_item()
        self.item_scores_ = bayesian_average(sums, counts, train.global_mean, self.prior_weight)
        self._train = train
        return self

    def score_items(self, user: int) -> np.ndarray:
        """Return the same damped mean for every user (the user is ignored)."""
        _ = self.train
        assert self.item_scores_ is not None
        return self.item_scores_.copy()
