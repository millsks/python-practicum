"""Milestones 6-7: evaluation metrics, model comparison, and the recommend() API."""

import numpy as np
import pandas as pd
import pytest
from recommender.api import Recommendation, RecommenderService
from recommender.base import Recommender
from recommender.baseline import PopularityRecommender
from recommender.data import RatingMatrix, build_matrix, generate_ratings
from recommender.evaluate import (
    EvaluationResult,
    compare_models,
    coverage,
    evaluate,
    format_table,
    precision_at_k,
    recall_at_k,
    top_k,
    train_test_split_by_user,
)
from recommender.mf import MatrixFactorization


class Oracle(Recommender):
    """A stub model with a fixed score table: ``scores[user, item]``."""

    def __init__(self, scores: np.ndarray) -> None:
        """Store the table."""
        self.scores = scores

    def fit(self, train: RatingMatrix) -> "Oracle":
        """Remember the training matrix."""
        self._train = train
        return self

    def score_items(self, user: int) -> np.ndarray:
        """Return the user's row of the table."""
        return self.scores[user].astype(float)


def small_data() -> RatingMatrix:
    df = pd.DataFrame(
        {
            "user_id": ["a", "a", "a", "b", "b"],
            "item_id": ["x", "y", "z", "x", "w"],
            "rating": [5.0, 2.0, 4.0, 3.0, 4.0],
        }
    )
    return build_matrix(df)


# --- Milestone 6: evaluation ---------------------------------------------------------------------


def test_top_k_orders_excludes_and_breaks_ties_by_index():
    scores = np.array([0.5, 0.9, 0.9, 0.1, 0.7])
    assert top_k(scores, 3) == [1, 2, 4], "highest first; tie 1 vs 2 broken by lower index"
    assert top_k(scores, 3, exclude=[1, 4]) == [2, 0, 3], "excluded items never appear"
    assert top_k(scores, 10, exclude=[0, 1, 2, 3]) == [4], "never more items than remain"
    with pytest.raises(ValueError):
        top_k(scores, 0)


def test_precision_and_recall_hand_computed():
    recommended = [3, 7, 1, 9, 4]
    relevant = {7, 4, 8}
    assert precision_at_k(recommended, relevant, 5) == pytest.approx(2 / 5), "2 hits in 5"
    assert recall_at_k(recommended, relevant, 5) == pytest.approx(2 / 3), "found 2 of 3 relevant"
    assert precision_at_k(recommended, relevant, 2) == pytest.approx(1 / 2), "only the first k count"
    assert recall_at_k(recommended, set(), 5) == 0.0, "no relevant items -> recall 0"


def test_precision_divides_by_k_even_for_short_lists():
    assert precision_at_k([1], {1}, 4) == pytest.approx(0.25), "a 1-item list at k=4 has precision 1/4"


def test_coverage_hand_computed():
    assert coverage([[0, 1], [1, 2], [2]], 6) == pytest.approx(0.5), "items 0, 1, 2 of 6 appear"
    assert coverage([], 4) == 0.0, "no lists -> nothing covered"
    with pytest.raises(ValueError):
        coverage([[0]], 0)


def test_split_partitions_each_users_ratings():
    data = build_matrix(generate_ratings(30, 40, seed=1, density=0.25))
    train, test = train_test_split_by_user(data, 0.2, seed=0)
    assert train.nnz + len(test) == data.nnz, "every rating goes to exactly one side"
    assert train.user_ids == data.user_ids and train.item_ids == data.item_ids, "same id mappings"
    for row in test:
        u, i = int(row[0]), int(row[1])
        assert train.matrix[u, i] == 0, "a test rating must not also be in train"
        assert data.matrix[u, i] == row[2], "test rows keep the original rating"
    test_users = set(test[:, 0].astype(int))
    assert test_users == set(range(data.n_users)), "every eligible user contributes test ratings"
    for u in range(data.n_users):
        assert len(train.user_ratings(u)[0]) >= 1, "every user keeps training ratings"


def test_split_is_deterministic_and_respects_min_ratings():
    data = small_data()
    _, t1 = train_test_split_by_user(data, 0.5, seed=3, min_ratings=3)
    _, t2 = train_test_split_by_user(data, 0.5, seed=3, min_ratings=3)
    np.testing.assert_array_equal(t1, t2, err_msg="same seed -> same split")
    assert set(t1[:, 0].astype(int)) == {0}, "user b has only 2 ratings, below min_ratings=3, so stays in train"
    with pytest.raises(ValueError):
        train_test_split_by_user(data, 1.0)


def test_evaluate_with_oracle_scores():
    data = small_data()
    train = data.with_matrix(data.matrix.copy())
    train.matrix[0, data.item_index["z"]] = 0
    train.matrix.eliminate_zeros()
    test = np.array([[0.0, data.item_index["z"], 4.0]])
    scores = np.zeros((2, 4))
    scores[0] = [1.0, 3.0, 2.0, 4.5]
    model = Oracle(scores).fit(train)
    result = evaluate(model, test, k=1, threshold=4.0)
    assert result.rmse == pytest.approx(0.5), "predicted 4.5 for a true 4"
    assert result.precision == pytest.approx(1.0), "the top unseen item for user a is z, which is relevant"
    assert result.recall == pytest.approx(1.0), "the only relevant item was found"
    assert result.coverage == pytest.approx(1 / 4), "one item of four was recommended"


def test_compare_models_and_table():
    data = build_matrix(generate_ratings(25, 30, seed=2, density=0.3))
    train, test = train_test_split_by_user(data, 0.25, seed=1)
    results = compare_models({"pop": PopularityRecommender(), "mf": MatrixFactorization(n_epochs=3)}, train, test, k=5)
    assert list(results) == ["pop", "mf"], "results keep the input order"
    assert all(isinstance(r, EvaluationResult) for r in results.values()), "one EvaluationResult per model"
    table = format_table(results, k=5)
    assert table.splitlines()[0] == "| model | RMSE | precision@5 | recall@5 | coverage |", "header names the metrics"
    assert len(table.splitlines()) == 4, "header, separator, one row per model"


def test_popularity_has_low_coverage():
    data = build_matrix(generate_ratings(40, 60, seed=5, density=0.2))
    train, test = train_test_split_by_user(data, 0.2, seed=0)
    result = evaluate(PopularityRecommender().fit(train), test, k=5)
    assert result.coverage < 0.5, "recommending the same hits to everyone covers little of the catalogue"


def test_matrix_factorization_beats_popularity_on_synthetic_data():
    data = build_matrix(generate_ratings(200, 120, seed=11))
    train, test = train_test_split_by_user(data, 0.2, seed=11)
    baseline = evaluate(PopularityRecommender().fit(train), test)
    mf = evaluate(MatrixFactorization(n_factors=3, lr=0.03, n_epochs=30, seed=0).fit(train), test)
    assert mf.rmse < baseline.rmse - 0.1, (
        f"MF should learn the latent tastes: MF RMSE {mf.rmse:.3f} vs popularity {baseline.rmse:.3f}"
    )


# --- Milestone 7: recommend() API ----------------------------------------------------------------


def oracle_service() -> RecommenderService:
    scores = np.array([[0.1, 0.9, 0.5, 0.7], [0.4, 0.3, 0.2, 0.1]])
    return RecommenderService(Oracle(scores)).fit(small_data())


def test_recommend_excludes_seen_items():
    service = oracle_service()
    recs = service.recommend("a", k=3)
    assert [r.item_id for r in recs] == ["w"], "user a rated x, y, z; only w is left"
    assert isinstance(recs[0], Recommendation) and recs[0].score == pytest.approx(0.1), "score comes from the model"


def test_recommend_can_include_seen_items():
    service = oracle_service()
    recs = service.recommend("a", k=2, exclude_seen=False)
    assert [r.item_id for r in recs] == ["x", "z"], "items are w, x, y, z; top scores are x=0.9 and z=0.7"


def test_recommend_unknown_user_gets_popularity():
    service = oracle_service()
    recs = service.recommend("new-user", k=2)
    assert [r.item_id for r in recs] == ["x", "w"], "cold users get the Bayesian-average ranking"


def test_recommend_validates_arguments_and_fit():
    with pytest.raises(ValueError):
        oracle_service().recommend("a", k=0)
    with pytest.raises(RuntimeError):
        RecommenderService(PopularityRecommender()).recommend("a")


def test_recommend_end_to_end_with_mf():
    data = build_matrix(generate_ratings(30, 25, seed=6, density=0.3))
    service = RecommenderService(MatrixFactorization(n_factors=4, n_epochs=5)).fit(data)
    user = data.user_ids[0]
    recs = service.recommend(user, k=5)
    seen = {data.item_ids[i] for i in data.user_ratings(0)[0]}
    assert len(recs) == 5, "k recommendations"
    assert not seen & {r.item_id for r in recs}, "no already-rated items"
    assert [r.score for r in recs] == sorted((r.score for r in recs), reverse=True), "best first"
