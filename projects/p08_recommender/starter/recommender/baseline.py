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
    # TODO: (prior_weight * prior_mean + sums) / (prior_weight + counts), element-wise.
    # TODO: Avoid dividing by zero: where the denominator is 0, return prior_mean.
    raise NotImplementedError


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
        # TODO: Column sums of train.matrix, counts_per_item(), then bayesian_average.
        # TODO: Store the scores in self.item_scores_ and the matrix in self._train.
        raise NotImplementedError

    def score_items(self, user: int) -> np.ndarray:
        """Return the same damped mean for every user (the user is ignored)."""
        # TODO: Everyone gets the same scores; return a copy of self.item_scores_.
        raise NotImplementedError
