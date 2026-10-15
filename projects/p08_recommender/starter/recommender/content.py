"""Content-based recommendation from genre vectors, and a weighted hybrid of models."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Self

import numpy as np
import pandas as pd

from recommender.base import Recommender
from recommender.data import GENRES, RatingMatrix


def genre_matrix(items: pd.DataFrame, item_ids: Sequence[str], genres: Sequence[str] = GENRES) -> np.ndarray:
    """One-hot encode each item's ``|``-separated genres, aligned to ``item_ids``.

    Args:
        items: Metadata with ``item_id`` and ``genres`` columns.
        item_ids: Column order of the rating matrix.
        genres: The genre vocabulary (column order of the result).

    Returns:
        A ``(len(item_ids), len(genres))`` array of 0/1; items without metadata get an all-zero row.
    """
    # TODO: One row per item id, one column per genre; 1.0 where the item has that genre.
    raise NotImplementedError


class ContentRecommender(Recommender):
    """Content-based filtering: like item-item kNN, but similarity comes from genre vectors.

    Because similarity does not depend on ratings, this works for cold items that nobody has rated yet.

    Args:
        item_features: ``(n_items, n_features)`` array aligned with the rating matrix columns.
        k: Number of similar rated items per prediction.
    """

    def __init__(self, item_features: np.ndarray, k: int = 20) -> None:
        """Store the item features and neighborhood size."""
        self.item_features = np.asarray(item_features, dtype=float)
        self.k = k
        self.similarity_: np.ndarray | None = None

    def fit(self, train: RatingMatrix) -> Self:
        """Compute the item-item cosine similarity of the feature vectors.

        Args:
            train: Training ratings.

        Returns:
            ``self``.

        Raises:
            ValueError: If the features do not have one row per item, or ``k < 1``.
        """
        # TODO: Check feature rows == n_items and k >= 1; similarity = cosine of feature vectors.
        raise NotImplementedError

    def score_items(self, user: int) -> np.ndarray:
        """Predict a rating for every item from genre similarity to the user's rated items."""
        # TODO: Same formula as ItemKNN.score_items, but with genre similarity.
        raise NotImplementedError


class HybridRecommender(Recommender):
    """Blend several models with fixed weights: ``sum(w * score) / sum(w)``.

    Args:
        components: ``(model, weight)`` pairs; weights must be non-negative and not all zero.
    """

    def __init__(self, components: Sequence[tuple[Recommender, float]]) -> None:
        """Validate and store the components.

        Raises:
            ValueError: If there are no components or the weights are invalid.
        """
        # TODO: Validate the weights, keep the components, normalize weights to sum to 1.
        raise NotImplementedError

    def fit(self, train: RatingMatrix) -> Self:
        """Fit every component on the same training ratings.

        Args:
            train: Training ratings.

        Returns:
            ``self``.
        """
        # TODO: Fit every component on train.
        raise NotImplementedError

    def score_items(self, user: int) -> np.ndarray:
        """Return the weighted average of the components' scores."""
        # TODO: Weighted sum of the components' score_items(user).
        raise NotImplementedError
