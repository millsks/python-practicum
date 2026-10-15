"""Matrix factorization with biases, trained by stochastic gradient descent."""

from __future__ import annotations

from typing import Self

import numpy as np

from recommender.base import Recommender
from recommender.data import RatingMatrix


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root mean squared error.

    Args:
        actual: True ratings.
        predicted: Predicted ratings, same length.

    Returns:
        ``sqrt(mean((actual - predicted) ** 2))``.

    Raises:
        ValueError: If the arrays are empty or have different lengths.
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.shape != predicted.shape or actual.size == 0:
        raise ValueError("rmse needs two non-empty arrays of the same shape")
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


class MatrixFactorization(Recommender):
    """Biased matrix factorization: ``r_ui ~ mu + b_u + b_i + p_u . q_i``.

    Training minimizes squared error plus L2 regularization on biases and factors with SGD, one
    shuffled pass over the ratings per epoch.

    Args:
        n_factors: Latent dimensions per user and item.
        lr: SGD learning rate.
        reg: L2 regularization strength.
        n_epochs: Passes over the training ratings.
        seed: Seed for initialization and shuffling.
        clip: Clamp predictions to this ``(low, high)`` rating range.
    """

    def __init__(
        self,
        n_factors: int = 5,
        lr: float = 0.02,
        reg: float = 0.1,
        n_epochs: int = 30,
        seed: int = 0,
        clip: tuple[float, float] = (1.0, 5.0),
    ) -> None:
        """Store hyperparameters."""
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.n_epochs = n_epochs
        self.seed = seed
        self.clip = clip
        self.history_: list[float] = []
        self.validation_history_: list[float] = []
        self.mu_ = 0.0
        self.user_bias_ = np.zeros(0)
        self.item_bias_ = np.zeros(0)
        self.user_factors_ = np.zeros((0, n_factors))
        self.item_factors_ = np.zeros((0, n_factors))

    def fit(self, train: RatingMatrix, validation: np.ndarray | None = None) -> Self:
        """Learn biases and factors with SGD, recording RMSE after each epoch.

        Args:
            train: Training ratings.
            validation: Optional ``(user, item, rating)`` rows; when given, ``validation_history_`` records
                their RMSE per epoch.

        Returns:
            ``self``.

        Raises:
            ValueError: If a hyperparameter is out of range or there are no ratings.
        """
        if self.n_factors < 1 or self.n_epochs < 1 or self.lr <= 0 or self.reg < 0:
            raise ValueError("need n_factors >= 1, n_epochs >= 1, lr > 0, reg >= 0")
        if train.nnz == 0:
            raise ValueError("cannot fit on an empty rating matrix")
        rng = np.random.default_rng(self.seed)
        self._train = train
        self.mu_ = train.global_mean
        self.user_bias_ = np.zeros(train.n_users)
        self.item_bias_ = np.zeros(train.n_items)
        self.user_factors_ = rng.normal(0.0, 0.1, size=(train.n_users, self.n_factors))
        self.item_factors_ = rng.normal(0.0, 0.1, size=(train.n_items, self.n_factors))
        triples = train.triples()
        users = triples[:, 0].astype(int)
        items = triples[:, 1].astype(int)
        ratings = triples[:, 2]
        self.history_ = []
        self.validation_history_ = []
        lr, reg = self.lr, self.reg
        for _ in range(self.n_epochs):
            for idx in rng.permutation(len(ratings)):
                u, i = users[idx], items[idx]
                pu, qi = self.user_factors_[u], self.item_factors_[i]
                err = ratings[idx] - (self.mu_ + self.user_bias_[u] + self.item_bias_[i] + pu @ qi)
                self.user_bias_[u] += lr * (err - reg * self.user_bias_[u])
                self.item_bias_[i] += lr * (err - reg * self.item_bias_[i])
                self.user_factors_[u] = pu + lr * (err * qi - reg * pu)
                self.item_factors_[i] = qi + lr * (err * pu - reg * qi)
            self.history_.append(rmse(ratings, self._raw(users, items)))
            if validation is not None and len(validation):
                self.validation_history_.append(rmse(validation[:, 2], self.predict_many(validation)))
        return self

    def _raw(self, users: np.ndarray, items: np.ndarray) -> np.ndarray:
        dots = np.einsum("ij,ij->i", self.user_factors_[users], self.item_factors_[items])
        raw: np.ndarray = self.mu_ + self.user_bias_[users] + self.item_bias_[items] + dots
        return raw

    def score_items(self, user: int) -> np.ndarray:
        """Predict a clipped rating for every item for one user."""
        _ = self.train
        raw: np.ndarray = (
            self.mu_ + self.user_bias_[user] + self.item_bias_ + self.item_factors_ @ self.user_factors_[user]
        )
        clipped: np.ndarray = np.clip(raw, *self.clip)
        return clipped
