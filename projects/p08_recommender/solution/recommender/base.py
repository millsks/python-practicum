"""The interface every recommender model implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self

import numpy as np

from recommender.data import RatingMatrix


class NotFittedError(RuntimeError):
    """Raised when a model is used before :meth:`Recommender.fit`."""


class Recommender(ABC):
    """Base class: fit on a :class:`RatingMatrix`, then score every item for a user.

    Subclasses implement :meth:`fit` and :meth:`score_items`; scores are predicted ratings on the
    1-5 scale, so they double as rating predictions for RMSE.
    """

    _train: RatingMatrix | None = None

    @property
    def train(self) -> RatingMatrix:
        """The matrix the model was fitted on.

        Raises:
            NotFittedError: If :meth:`fit` has not been called.
        """
        if self._train is None:
            raise NotFittedError(f"{type(self).__name__} is not fitted; call fit() first")
        return self._train

    @abstractmethod
    def fit(self, train: RatingMatrix) -> Self:
        """Learn from the training ratings and return ``self``."""

    @abstractmethod
    def score_items(self, user: int) -> np.ndarray:
        """Return a predicted rating for every item for user row ``user``."""

    def predict(self, user: int, item: int) -> float:
        """Predict one rating.

        Args:
            user: User row index.
            item: Item column index.

        Returns:
            The predicted rating.
        """
        return float(self.score_items(user)[item])

    def predict_many(self, pairs: np.ndarray) -> np.ndarray:
        """Predict ratings for an array of ``(user, item, ...)`` rows, scoring each user once.

        Args:
            pairs: Array whose first two columns are user and item indices.

        Returns:
            One prediction per row.
        """
        out = np.empty(len(pairs), dtype=float)
        users = pairs[:, 0].astype(int)
        items = pairs[:, 1].astype(int)
        for u in np.unique(users):
            mask = users == u
            out[mask] = self.score_items(int(u))[items[mask]]
        return out
