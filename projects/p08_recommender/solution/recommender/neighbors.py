"""Neighborhood collaborative filtering: item-item and user-user kNN with cosine similarity."""

from __future__ import annotations

from typing import Self

import numpy as np
from scipy.sparse import csr_matrix, diags

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
    sparse = csr_matrix(rows, dtype=float)
    norms = np.sqrt(np.asarray(sparse.multiply(sparse).sum(axis=1)).ravel())
    inverse = np.divide(1.0, norms, out=np.zeros_like(norms), where=norms > 0)
    unit = diags(inverse) @ sparse
    sim = np.asarray((unit @ unit.T).todense(), dtype=float)
    return np.clip(sim, -1.0, 1.0)


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
    if k < 1:
        raise ValueError("k must be >= 1")
    sims = np.where(similarities > 0, similarities, 0.0)
    if sims.shape[1] <= k:
        return sims
    cutoff = np.argpartition(-sims, k - 1, axis=1)[:, :k]
    kept = np.zeros_like(sims)
    rows = np.arange(sims.shape[0])[:, None]
    kept[rows, cutoff] = sims[rows, cutoff]
    return kept


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
        if self.k < 1:
            raise ValueError("k must be >= 1")
        self.similarity_ = cosine_similarity(train.matrix.T)
        self._train = train
        return self

    def score_items(self, user: int) -> np.ndarray:
        """Predict a rating for every item for one user."""
        train = self.train
        assert self.similarity_ is not None
        items, ratings = train.user_ratings(user)
        if len(items) == 0:
            return np.full(train.n_items, train.global_mean)
        mean = float(ratings.mean())
        weights = top_k_mask(self.similarity_[:, items], self.k)
        numerator = weights @ (ratings - mean)
        denominator = weights.sum(axis=1)
        safe = np.where(denominator > 0, denominator, 1.0)
        return mean + np.where(denominator > 0, numerator / safe, 0.0)


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
        if self.k < 1:
            raise ValueError("k must be >= 1")
        counts = np.diff(train.matrix.indptr)
        sums = np.asarray(train.matrix.sum(axis=1)).ravel()
        safe = np.where(counts > 0, counts, 1)
        self.user_means_ = np.where(counts > 0, sums / safe, train.global_mean)
        self.similarity_ = cosine_similarity(train.matrix)
        self._train = train
        return self

    def score_items(self, user: int) -> np.ndarray:
        """Predict a rating for every item for one user."""
        train = self.train
        assert self.similarity_ is not None and self.user_means_ is not None
        sims = self.similarity_[user].copy()
        sims[user] = 0.0
        order = np.flatnonzero(sims > 0)
        order = order[np.argsort(-sims[order], kind="stable")]
        mean = float(self.user_means_[user])
        if len(order) == 0:
            return np.full(train.n_items, mean)
        dense = train.matrix[order].toarray()
        rated = dense > 0
        deviations = np.where(rated, dense - self.user_means_[order][:, None], 0.0)
        keep = rated & (np.cumsum(rated, axis=0) <= self.k)
        weights = sims[order][:, None] * keep
        numerator = (weights * deviations).sum(axis=0)
        denominator = weights.sum(axis=0)
        safe = np.where(denominator > 0, denominator, 1.0)
        return mean + np.where(denominator > 0, numerator / safe, 0.0)
