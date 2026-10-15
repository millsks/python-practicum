"""Content-based recommendation from genre vectors, and a weighted hybrid of models."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Self

import numpy as np
import pandas as pd

from recommender.base import Recommender
from recommender.data import GENRES, RatingMatrix
from recommender.neighbors import cosine_similarity, top_k_mask


def genre_matrix(items: pd.DataFrame, item_ids: Sequence[str], genres: Sequence[str] = GENRES) -> np.ndarray:
    """One-hot encode each item's ``|``-separated genres, aligned to ``item_ids``.

    Args:
        items: Metadata with ``item_id`` and ``genres`` columns.
        item_ids: Column order of the rating matrix.
        genres: The genre vocabulary (column order of the result).

    Returns:
        A ``(len(item_ids), len(genres))`` array of 0/1; items without metadata get an all-zero row.
    """
    vocabulary = {g: c for c, g in enumerate(genres)}
    lookup = dict(zip(items["item_id"].astype(str), items["genres"].fillna(""), strict=True))
    out = np.zeros((len(item_ids), len(genres)))
    for row, iid in enumerate(item_ids):
        for genre in str(lookup.get(iid, "")).split("|"):
            if genre in vocabulary:
                out[row, vocabulary[genre]] = 1.0
    return out


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
        if self.item_features.shape[0] != train.n_items:
            raise ValueError("item_features needs one row per item in the rating matrix")
        if self.k < 1:
            raise ValueError("k must be >= 1")
        self.similarity_ = cosine_similarity(self.item_features)
        self._train = train
        return self

    def score_items(self, user: int) -> np.ndarray:
        """Predict a rating for every item from genre similarity to the user's rated items."""
        train = self.train
        assert self.similarity_ is not None
        items, ratings = train.user_ratings(user)
        if len(items) == 0:
            return np.full(train.n_items, train.global_mean)
        mean = float(ratings.mean())
        weights = top_k_mask(self.similarity_[:, items], self.k)
        denominator = weights.sum(axis=1)
        safe = np.where(denominator > 0, denominator, 1.0)
        return mean + np.where(denominator > 0, (weights @ (ratings - mean)) / safe, 0.0)


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
        weights = np.array([w for _, w in components], dtype=float)
        if len(components) == 0 or (weights < 0).any() or weights.sum() == 0:
            raise ValueError("need at least one component with non-negative weights that are not all zero")
        self.components = list(components)
        self.weights = weights / weights.sum()

    def fit(self, train: RatingMatrix) -> Self:
        """Fit every component on the same training ratings.

        Args:
            train: Training ratings.

        Returns:
            ``self``.
        """
        for model, _ in self.components:
            model.fit(train)
        self._train = train
        return self

    def score_items(self, user: int) -> np.ndarray:
        """Return the weighted average of the components' scores."""
        _ = self.train
        scores = np.stack([model.score_items(user) for model, _ in self.components])
        blended: np.ndarray = self.weights @ scores
        return blended
