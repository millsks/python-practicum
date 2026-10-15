"""Neighborhood collaborative filtering: item-item and user-user kNN with cosine similarity."""

from __future__ import annotations

from typing import Self

import numpy as np
from scipy.sparse import csr_matrix

from recommender.base import Recommender
from recommender.data import RatingMatrix


def cosine_similarity(rows: csr_matrix | np.ndarray) -> np.ndarray:
    """Return the cosine similarity between every pair of rows.

    Rows that are all zero (for example a cold item with no ratings) get similarity ``0`` with
    everything, including themselves, instead of dividing by zero.

    Args:
        rows: Sparse or dense 2-D array; each row is a vector.

    Returns:
        A dense ``(n_rows, n_rows)`` array with values in ``[-1, 1]``.
    """
    # TODO: Normalize each row to unit length (rows of zeros stay zero), then unit @ unit.T.
    # TODO: Return a dense array; clip to [-1, 1] to absorb rounding.
    raise NotImplementedError


def top_k_mask(similarities: np.ndarray, k: int) -> np.ndarray:
    """Keep only the ``k`` largest positive similarities in each row.

    Args:
        similarities: ``(n_targets, n_neighbors)`` array.
        k: Neighbors to keep per row (``>= 1``).

    Returns:
        A copy where everything except each row's top-``k`` positive values is ``0``.

    Raises:
        ValueError: If ``k < 1``.
    """
    # TODO: Zero out non-positive values, then keep only the k largest per row (np.argpartition).
    raise NotImplementedError


class ItemKNN(Recommender):
    """Item-item collaborative filtering.

    The prediction for user ``u`` and item ``i`` is the user's mean plus the similarity-weighted average of
    the user's deviations from that mean on the ``k`` rated items most similar to ``i``. Items with no
    similar rated items (including cold items) fall back to the user's mean.

    Args:
        k: Number of neighbors per prediction.
    """

    def __init__(self, k: int = 20) -> None:
        """Store the neighborhood size."""
        self.k = k
        self.similarity_: np.ndarray | None = None

    def fit(self, train: RatingMatrix) -> Self:
        """Compute the item-item cosine similarity matrix.

        Args:
            train: Training ratings.

        Returns:
            ``self``.

        Raises:
            ValueError: If ``k < 1``.
        """
        # TODO: Similarity between items = cosine_similarity of the item vectors (train.matrix.T).
        raise NotImplementedError

    def score_items(self, user: int) -> np.ndarray:
        """Predict a rating for every item for one user."""
        # TODO: Cold user -> global mean. Otherwise mean + weighted average of the user's deviations,
        # TODO: weights = top_k_mask(similarity[:, rated_items], k). No positive weight -> user mean.
        raise NotImplementedError


class UserKNN(Recommender):
    """User-user collaborative filtering.

    The prediction for user ``u`` and item ``i`` is ``u``'s mean plus the similarity-weighted average of
    how much the ``k`` most similar users who rated ``i`` deviated from *their* means.

    Args:
        k: Number of neighbors per prediction.
    """

    def __init__(self, k: int = 20) -> None:
        """Store the neighborhood size."""
        self.k = k
        self.similarity_: np.ndarray | None = None
        self.user_means_: np.ndarray | None = None

    def fit(self, train: RatingMatrix) -> Self:
        """Compute user means and the user-user cosine similarity matrix.

        Args:
            train: Training ratings.

        Returns:
            ``self``.

        Raises:
            ValueError: If ``k < 1``.
        """
        # TODO: Compute each user's mean rating (global mean if none) and user-user cosine similarity.
        raise NotImplementedError

    def score_items(self, user: int) -> np.ndarray:
        """Predict a rating for every item for one user."""
        # TODO: Sort the other users by similarity (positive only). For each item use the first k who rated it:
        # TODO: mean_u + sum(sim * (r_vi - mean_v)) / sum(sim). No neighbors -> mean_u.
        raise NotImplementedError
