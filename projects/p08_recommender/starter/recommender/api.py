"""The public recommendation API and a small command-line demo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from recommender.base import Recommender
from recommender.baseline import PopularityRecommender
from recommender.data import RatingMatrix


@dataclass(frozen=True, slots=True)
class Recommendation:
    """One recommended item.

    Attributes:
        item_id: External item id.
        score: The model's predicted rating.
    """

    item_id: str
    score: float


class RecommenderService:
    """Serve top-k recommendations by external id, with a popularity fallback for unknown users.

    Args:
        model: Any recommender model (fitted by :meth:`fit`).
        fallback: Model used for users not in the training data; defaults to a popularity baseline.
    """

    def __init__(self, model: Recommender, fallback: Recommender | None = None) -> None:
        """Store the model and fallback."""
        self.model = model
        self.fallback = fallback if fallback is not None else PopularityRecommender()
        self._data: RatingMatrix | None = None

    def fit(self, data: RatingMatrix) -> Self:
        """Fit the model and the fallback on ``data``.

        Args:
            data: Ratings to learn from.

        Returns:
            ``self``.
        """
        # TODO: Fit the model and the fallback; remember the data.
        raise NotImplementedError

    def recommend(self, user_id: str, k: int = 10, exclude_seen: bool = True) -> list[Recommendation]:
        """Return the top ``k`` items for a user, best first.

        Args:
            user_id: External user id; unknown users get the fallback ranking.
            k: Number of items (``>= 1``).
            exclude_seen: Skip items the user already rated.

        Returns:
            Up to ``k`` recommendations.

        Raises:
            ValueError: If ``k < 1``.
            RuntimeError: If the service is not fitted.
        """
        # TODO: Validate k and fitted state. Unknown user -> fallback scores, nothing excluded.
        # TODO: Known user -> model scores, excluding seen items if exclude_seen. Use top_k.
        raise NotImplementedError


def main() -> None:
    """Compare every model on synthetic data and print the table plus sample recommendations."""
    from recommender.content import ContentRecommender, HybridRecommender, genre_matrix
    from recommender.data import build_matrix, generate_items, generate_ratings
    from recommender.evaluate import compare_models, format_table, train_test_split_by_user
    from recommender.mf import MatrixFactorization
    from recommender.neighbors import ItemKNN, UserKNN

    n_users, n_items, seed = 300, 200, 7
    ratings = generate_ratings(n_users, n_items, seed)
    items = generate_items(n_items, seed)
    data = build_matrix(ratings, item_ids=items["item_id"].tolist())
    train, test = train_test_split_by_user(data, 0.2, seed=seed)
    genres = genre_matrix(items, data.item_ids)
    models: dict[str, Recommender] = {
        "popularity": PopularityRecommender(),
        "item-knn": ItemKNN(k=30),
        "user-knn": UserKNN(k=30),
        "content": ContentRecommender(genres),
        "mf": MatrixFactorization(n_factors=3, lr=0.03, n_epochs=30, seed=seed),
        "hybrid": HybridRecommender(
            [
                (MatrixFactorization(n_factors=3, lr=0.03, n_epochs=30, seed=seed), 0.8),
                (ContentRecommender(genres), 0.2),
            ]
        ),
    }
    print(format_table(compare_models(models, train, test)))
    service = RecommenderService(MatrixFactorization(n_factors=3, lr=0.03, n_epochs=30, seed=seed)).fit(data)
    for rec in service.recommend(data.user_ids[0], k=5):
        print(f"{rec.item_id}\t{rec.score:.2f}")


if __name__ == "__main__":
    main()
