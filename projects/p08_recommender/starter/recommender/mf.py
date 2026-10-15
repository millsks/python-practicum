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
    # TODO: sqrt(mean((actual - predicted) ** 2)); raise ValueError on empty or mismatched input.
    raise NotImplementedError


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
        # TODO: Validate hyperparameters. Init biases at 0 and factors ~ N(0, 0.1) with the seeded rng.
        # TODO: Each epoch: visit ratings in a shuffled order; err = r - prediction;
        # TODO: b_u += lr * (err - reg * b_u); same for b_i; p_u += lr * (err * q_i - reg * p_u); same for q_i.
        # TODO: Append training RMSE to history_ (and validation RMSE when validation is given).
        raise NotImplementedError

    def _raw(self, users: np.ndarray, items: np.ndarray) -> np.ndarray:
        # TODO: mu + b_u + b_i + row-wise dot of user and item factors (np.einsum or sum of products).
        raise NotImplementedError

    def score_items(self, user: int) -> np.ndarray:
        """Predict a clipped rating for every item for one user."""
        # TODO: Predict all items for one user, then np.clip to self.clip.
        raise NotImplementedError
