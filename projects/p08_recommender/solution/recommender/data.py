"""Synthetic ratings, item metadata, and the sparse user x item rating matrix."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

GENRES: tuple[str, ...] = ("Action", "Drama", "Comedy", "Horror", "Sci-Fi", "Romance")
N_FACTORS = 3
RATING_COLUMNS: tuple[str, ...] = ("user_id", "item_id", "rating")


def _item_factors(n_items: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng([seed, 1])
    factors = rng.normal(0.0, 1.0, size=(n_items, N_FACTORS))
    bias = rng.normal(0.0, 0.5, size=n_items)
    return factors, bias


def _user_factors(n_users: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng([seed, 2])
    factors = rng.normal(0.0, 1.0, size=(n_users, N_FACTORS))
    bias = rng.normal(0.0, 0.3, size=n_users)
    return factors, bias


def user_id(index: int) -> str:
    """Return the synthetic id for a user index (``u0001`` style)."""
    return f"u{index + 1:04d}"


def item_id(index: int) -> str:
    """Return the synthetic id for an item index (``m0001`` style)."""
    return f"m{index + 1:04d}"


def generate_ratings(n_users: int, n_items: int, seed: int = 0, *, density: float = 0.15) -> pd.DataFrame:
    """Generate a deterministic synthetic ratings table driven by latent tastes.

    Each user and item gets a hidden 3-dimensional taste vector plus a bias. The true rating is
    ``3 + user_bias + item_bias + 1.2 * dot(user, item) / sqrt(3)`` plus noise, rounded to 1..5. Popular
    items (higher item bias) are rated more often, like a real catalogue.

    Args:
        n_users: Number of users (at least 1).
        n_items: Number of items (at least 5).
        seed: Random seed; the same arguments always give the same table.
        density: Fraction of the catalogue each user rates (at least 5 items per user).

    Returns:
        A DataFrame with columns ``user_id``, ``item_id``, ``rating`` (float 1.0-5.0).

    Raises:
        ValueError: If the sizes or density are out of range.
    """
    if n_users < 1 or n_items < 5:
        raise ValueError("need at least 1 user and 5 items")
    if not 0.0 < density <= 1.0:
        raise ValueError("density must be in (0, 1]")
    item_vecs, item_bias = _item_factors(n_items, seed)
    user_vecs, user_bias = _user_factors(n_users, seed)
    rng = np.random.default_rng([seed, 3])
    per_user = min(n_items, max(5, round(density * n_items)))
    popularity = np.exp(item_bias)
    popularity /= popularity.sum()
    rows: list[tuple[str, str, float]] = []
    for u in range(n_users):
        chosen = np.sort(rng.choice(n_items, size=per_user, replace=False, p=popularity))
        signal = 1.2 * (item_vecs[chosen] @ user_vecs[u]) / np.sqrt(N_FACTORS)
        raw = 3.0 + user_bias[u] + item_bias[chosen] + signal + rng.normal(0.0, 0.4, size=per_user)
        values = np.clip(np.rint(raw), 1, 5)
        rows.extend((user_id(u), item_id(int(i)), float(v)) for i, v in zip(chosen, values, strict=True))
    return pd.DataFrame(rows, columns=list(RATING_COLUMNS))


def generate_items(n_items: int, seed: int = 0) -> pd.DataFrame:
    """Generate item metadata whose genres follow the same latent tastes as :func:`generate_ratings`.

    Each latent dimension maps to a pair of genres (positive side, negative side), so genre vectors carry
    real signal for content-based recommendation.

    Args:
        n_items: Number of items.
        seed: The seed passed to :func:`generate_ratings`.

    Returns:
        A DataFrame with columns ``item_id``, ``title``, ``genres`` (genres joined by ``|``).
    """
    item_vecs, _ = _item_factors(n_items, seed)
    records = []
    for i, vec in enumerate(item_vecs):
        genres = []
        for dim, value in enumerate(vec):
            if value > 0.5:
                genres.append(GENRES[2 * dim])
            elif value < -0.5:
                genres.append(GENRES[2 * dim + 1])
        if not genres:
            dim = int(np.argmax(np.abs(vec)))
            genres.append(GENRES[2 * dim] if vec[dim] >= 0 else GENRES[2 * dim + 1])
        records.append((item_id(i), f"Movie {i + 1:04d}", "|".join(genres)))
    return pd.DataFrame(records, columns=["item_id", "title", "genres"])


def load_ratings_csv(path: Path) -> pd.DataFrame:
    """Load a ratings CSV with ``user_id``, ``item_id``, ``rating`` columns.

    Args:
        path: CSV file to read.

    Returns:
        The ratings with string ids and float ratings.

    Raises:
        ValueError: If a required column is missing.
    """
    frame = pd.read_csv(path, dtype={"user_id": str, "item_id": str})
    missing = [c for c in RATING_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"ratings file is missing columns: {missing}")
    frame = frame.loc[:, list(RATING_COLUMNS)].copy()
    frame["rating"] = frame["rating"].astype(float)
    return frame


@dataclass(frozen=True)
class RatingMatrix:
    """A user x item rating matrix in CSR form plus the id mappings.

    A stored value of ``0`` means "not rated", so ratings must be positive.

    Attributes:
        matrix: Sparse ``(n_users, n_items)`` ratings.
        user_ids: External user id for each row.
        item_ids: External item id for each column.
    """

    matrix: csr_matrix
    user_ids: tuple[str, ...]
    item_ids: tuple[str, ...]

    @cached_property
    def user_index(self) -> dict[str, int]:
        """Map external user id to row index."""
        return {uid: i for i, uid in enumerate(self.user_ids)}

    @cached_property
    def item_index(self) -> dict[str, int]:
        """Map external item id to column index."""
        return {iid: j for j, iid in enumerate(self.item_ids)}

    @property
    def n_users(self) -> int:
        """Number of users (rows)."""
        return len(self.user_ids)

    @property
    def n_items(self) -> int:
        """Number of items (columns)."""
        return len(self.item_ids)

    @property
    def nnz(self) -> int:
        """Number of stored ratings."""
        return int(self.matrix.nnz)

    @cached_property
    def global_mean(self) -> float:
        """Mean of all stored ratings (``0.0`` when there are none)."""
        return float(self.matrix.data.mean()) if self.matrix.nnz else 0.0

    def user_ratings(self, user: int) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(item_indices, ratings)`` for one user row.

        Args:
            user: Row index.

        Returns:
            Two aligned arrays.
        """
        start, end = self.matrix.indptr[user], self.matrix.indptr[user + 1]
        return self.matrix.indices[start:end], self.matrix.data[start:end]

    def counts_per_item(self) -> np.ndarray:
        """Return the number of ratings each item has."""
        return np.bincount(self.matrix.indices, minlength=self.n_items)

    def triples(self) -> np.ndarray:
        """Return every rating as rows of ``(user_index, item_index, rating)`` floats."""
        coo = self.matrix.tocoo()
        return np.column_stack([coo.row, coo.col, coo.data]).astype(float)

    def with_matrix(self, matrix: csr_matrix) -> RatingMatrix:
        """Return a copy sharing the id mappings but holding different ratings."""
        return RatingMatrix(matrix=matrix, user_ids=self.user_ids, item_ids=self.item_ids)


def build_matrix(ratings: pd.DataFrame, *, item_ids: list[str] | None = None) -> RatingMatrix:
    """Build a :class:`RatingMatrix` from a ratings table.

    Users and items are indexed in sorted id order so the result is deterministic. Pass ``item_ids`` to
    include catalogue items that have no ratings yet (cold items).

    Args:
        ratings: Table with ``user_id``, ``item_id``, ``rating`` columns.
        item_ids: Optional full catalogue of item ids.

    Returns:
        The sparse matrix with its id mappings.

    Raises:
        ValueError: On duplicate (user, item) pairs, non-positive ratings, or items missing from ``item_ids``.
    """
    if ratings.duplicated(subset=["user_id", "item_id"]).any():
        raise ValueError("duplicate (user_id, item_id) ratings")
    values = ratings["rating"].to_numpy(dtype=float)
    if (values <= 0).any() or not np.isfinite(values).all():
        raise ValueError("ratings must be positive finite numbers (0 means 'unrated')")
    users = tuple(sorted(ratings["user_id"].astype(str).unique()))
    catalogue = sorted(set(item_ids)) if item_ids is not None else sorted(ratings["item_id"].astype(str).unique())
    items = tuple(catalogue)
    user_pos = {u: i for i, u in enumerate(users)}
    item_pos = {m: j for j, m in enumerate(items)}
    try:
        cols = [item_pos[str(m)] for m in ratings["item_id"]]
    except KeyError as exc:
        raise ValueError(f"item {exc.args[0]!r} is not in item_ids") from exc
    rows = [user_pos[str(u)] for u in ratings["user_id"]]
    matrix = csr_matrix((values, (rows, cols)), shape=(len(users), len(items)))
    matrix.sort_indices()
    return RatingMatrix(matrix=matrix, user_ids=users, item_ids=items)
