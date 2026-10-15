"""Milestones 2-5: popularity, neighborhood CF, matrix factorization, content, and hybrid models."""

import numpy as np
import pandas as pd
import pytest
from recommender.base import NotFittedError, Recommender
from recommender.baseline import PopularityRecommender, bayesian_average
from recommender.content import ContentRecommender, HybridRecommender, genre_matrix
from recommender.data import RatingMatrix, build_matrix
from recommender.mf import MatrixFactorization, rmse
from recommender.neighbors import ItemKNN, UserKNN, cosine_similarity, top_k_mask


def knn_data() -> RatingMatrix:
    """u0: i0=5, i1=1 (mean 3). u1: i0=4, i2=2 (mean 3). i3 is a cold item.

    Item columns: i0=[5, 4], i1=[1, 0], i2=[0, 2], i3=[0, 0]. i2 is similar to i0 only.
    """
    df = pd.DataFrame(
        {"user_id": ["u0", "u0", "u1", "u1"], "item_id": ["i0", "i1", "i0", "i2"], "rating": [5.0, 1.0, 4.0, 2.0]}
    )
    return build_matrix(df, item_ids=["i0", "i1", "i2", "i3"])


class FixedScores(Recommender):
    """A stub model that gives every user the same fixed scores."""

    def __init__(self, scores: list[float]) -> None:
        """Store the scores."""
        self.scores = np.array(scores)

    def fit(self, train: RatingMatrix) -> "FixedScores":
        """Remember the training matrix."""
        self._train = train
        return self

    def score_items(self, user: int) -> np.ndarray:
        """Return the fixed scores."""
        return self.scores.copy()


# --- Milestone 2: popularity baseline -------------------------------------------------------------


def test_bayesian_average_hand_computed():
    result = bayesian_average(np.array([9.0, 5.0, 0.0]), np.array([2, 1, 0]), prior_mean=3.0, prior_weight=2.0)
    np.testing.assert_allclose(result, [15 / 4, 11 / 3, 3.0], err_msg="(C*m + sum) / (C + n) per item")


def test_bayesian_average_zero_weight_is_plain_mean():
    result = bayesian_average(np.array([8.0, 0.0]), np.array([2, 0]), prior_mean=3.5, prior_weight=0.0)
    np.testing.assert_allclose(result, [4.0, 3.5], err_msg="no prior -> plain mean; unrated -> prior mean")
    with pytest.raises(ValueError):
        bayesian_average(np.array([1.0]), np.array([1]), 3.0, -1.0)


def test_popularity_prefers_many_good_ratings_over_one_perfect():
    df = pd.DataFrame(
        {
            "user_id": ["a", "b", "c", "d", "a", "c", "d"],
            "item_id": ["hit", "hit", "hit", "hit", "lucky", "flop", "flop"],
            "rating": [5.0, 5.0, 4.0, 5.0, 5.0, 1.0, 1.0],
        }
    )
    data = build_matrix(df, item_ids=["hit", "lucky", "flop", "cold"])
    scores = PopularityRecommender(prior_weight=3.0).fit(data).score_items(0)
    hit, lucky, cold = (data.item_index[name] for name in ("hit", "lucky", "cold"))
    mean = 26 / 7
    assert scores[hit] == pytest.approx((3 * mean + 19) / 7), "hit: (3*mean + 19) / (3 + 4)"
    assert scores[lucky] == pytest.approx((3 * mean + 5) / 4), "lucky: (3*mean + 5) / (3 + 1)"
    assert scores[cold] == pytest.approx(mean), "a cold item scores the global mean"
    assert scores[hit] > scores[lucky], "four good ratings beat one perfect rating"


def test_unfitted_model_raises():
    with pytest.raises(NotFittedError):
        PopularityRecommender().score_items(0)


# --- Milestone 3: neighborhood collaborative filtering ------------------------------------------


def test_cosine_similarity_hand_computed_and_zero_rows():
    sim = cosine_similarity(np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]))
    assert sim[0, 1] == pytest.approx(1 / np.sqrt(2)), "cos 45 degrees"
    assert sim[0, 0] == pytest.approx(1.0) and sim[1, 1] == pytest.approx(1.0), "self-similarity is 1"
    assert np.all(sim[2] == 0) and np.all(sim[:, 2] == 0), "an all-zero row has similarity 0, not NaN"


def test_cosine_similarity_accepts_sparse_and_is_symmetric():
    data = knn_data()
    sim = cosine_similarity(data.matrix.T)
    assert sim.shape == (4, 4), "one row/column per item"
    np.testing.assert_allclose(sim, sim.T, err_msg="cosine similarity is symmetric")
    assert sim[1, 2] == pytest.approx(0.0), "i1 and i2 share no raters"
    assert sim[0, 2] == pytest.approx(8 / (np.sqrt(41) * 2)), "i0 . i2 / (|i0| |i2|)"


def test_top_k_mask_keeps_largest_positive():
    kept = top_k_mask(np.array([[0.9, 0.1, 0.5, -0.3]]), 2)
    np.testing.assert_allclose(kept, [[0.9, 0.0, 0.5, 0.0]], err_msg="keep the 2 largest, zero the rest")
    np.testing.assert_allclose(top_k_mask(np.array([[0.2, -0.4]]), 5), [[0.2, 0.0]], err_msg="negatives dropped")
    with pytest.raises(ValueError):
        top_k_mask(np.zeros((1, 2)), 0)


def test_item_knn_hand_computed_prediction():
    model = ItemKNN(k=5).fit(knn_data())
    assert model.predict(0, 2) == pytest.approx(5.0), "u0 mean 3 + deviation of the only similar item i0 (+2)"


def test_item_knn_cold_item_falls_back_to_user_mean():
    model = ItemKNN(k=5).fit(knn_data())
    assert model.predict(0, 3) == pytest.approx(3.0), "the cold item i3 has no similar items -> user mean"
    assert model.predict(1, 3) == pytest.approx(3.0), "u1's mean is also 3"


def test_item_knn_rejects_bad_k():
    with pytest.raises(ValueError):
        ItemKNN(k=0).fit(knn_data())


def test_user_knn_hand_computed_prediction():
    model = UserKNN(k=5).fit(knn_data())
    assert model.predict(0, 2) == pytest.approx(2.0), "u0 mean 3 + u1's deviation on i2 (2 - 3 = -1)"
    assert model.predict(1, 1) == pytest.approx(1.0), "u1 mean 3 + u0's deviation on i1 (1 - 3 = -2)"
    assert model.predict(0, 3) == pytest.approx(3.0), "nobody rated i3 -> user mean"


def test_user_knn_without_neighbors_uses_own_mean():
    df = pd.DataFrame({"user_id": ["a", "b"], "item_id": ["x", "y"], "rating": [4.0, 2.0]})
    model = UserKNN(k=3).fit(build_matrix(df))
    np.testing.assert_allclose(model.score_items(0), [4.0, 4.0], err_msg="no similar users -> own mean everywhere")


# --- Milestone 4: matrix factorization ----------------------------------------------------------


def test_rmse_hand_computed():
    assert rmse(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 5.0])) == pytest.approx(np.sqrt(4 / 3)), "sqrt(4/3)"
    with pytest.raises(ValueError):
        rmse(np.array([]), np.array([]))


def test_mf_training_rmse_decreases():
    from recommender.data import generate_ratings

    data = build_matrix(generate_ratings(40, 30, seed=2, density=0.3))
    model = MatrixFactorization(n_factors=3, lr=0.03, n_epochs=15, seed=0).fit(data)
    assert len(model.history_) == 15, "one RMSE per epoch"
    assert model.history_[-1] < model.history_[0], "training RMSE should go down"
    assert model.history_[-1] < model.history_[0] - 0.15, f"RMSE should fall substantially: {model.history_}"


def test_mf_is_deterministic_and_clipped():
    from recommender.data import generate_ratings

    data = build_matrix(generate_ratings(20, 15, seed=4, density=0.4))
    a = MatrixFactorization(n_factors=3, n_epochs=5, seed=9).fit(data).score_items(0)
    b = MatrixFactorization(n_factors=3, n_epochs=5, seed=9).fit(data).score_items(0)
    np.testing.assert_allclose(a, b, err_msg="same seed -> same model")
    big = MatrixFactorization(n_factors=3, lr=0.05, n_epochs=40, reg=0.0, seed=1).fit(data)
    for user in range(data.n_users):
        scores = big.score_items(user)
        assert scores.min() >= 1.0 and scores.max() <= 5.0, "predictions are clipped to 1..5"


def test_mf_constant_ratings_predict_the_constant():
    df = pd.DataFrame({"user_id": ["a", "a", "b", "b", "c"], "item_id": ["x", "y", "x", "z", "y"], "rating": [4.0] * 5})
    model = MatrixFactorization(n_factors=2, n_epochs=20, seed=0).fit(build_matrix(df))
    assert model.predict(2, 2) == pytest.approx(4.0, abs=0.05), "if everyone rates 4, predict about 4"


def test_mf_validation_history_and_bad_params():
    df = pd.DataFrame({"user_id": ["a", "a", "b"], "item_id": ["x", "y", "x"], "rating": [5.0, 3.0, 4.0]})
    data = build_matrix(df)
    model = MatrixFactorization(n_factors=2, n_epochs=4).fit(data, validation=np.array([[1.0, 1.0, 3.0]]))
    assert len(model.validation_history_) == 4, "validation RMSE tracked per epoch"
    with pytest.raises(ValueError):
        MatrixFactorization(n_factors=0).fit(data)
    with pytest.raises(ValueError):
        MatrixFactorization(lr=0.0).fit(data)


# --- Milestone 5: content-based and hybrid -------------------------------------------------------


def test_genre_matrix_one_hot():
    items = pd.DataFrame({"item_id": ["a", "b"], "genres": ["Action|Comedy", "Drama|Western"]})
    g = genre_matrix(items, ["b", "a", "zzz"], genres=["Action", "Drama", "Comedy"])
    np.testing.assert_array_equal(
        g, [[0, 1, 0], [1, 0, 1], [0, 0, 0]], err_msg="rows follow item_ids; unknown genres and items -> 0"
    )


def test_content_model_scores_cold_items_from_genres():
    items = pd.DataFrame({"item_id": ["i0", "i1", "i2", "i3"], "genres": ["Action", "Romance", "Drama", "Action"]})
    data = knn_data()
    model = ContentRecommender(genre_matrix(items, data.item_ids), k=5).fit(data)
    assert model.predict(0, 3) == pytest.approx(5.0), "cold i3 shares Action with i0 (u0 deviation +2)"
    assert model.predict(0, 2) == pytest.approx(3.0), "Drama matches nothing u0 rated -> user mean"


def test_content_model_validates_feature_rows():
    with pytest.raises(ValueError):
        ContentRecommender(np.zeros((2, 3))).fit(knn_data())


def test_hybrid_is_weighted_average():
    data = knn_data()
    hybrid = HybridRecommender([(FixedScores([1, 2, 3, 4]), 3.0), (FixedScores([5, 2, 3, 0]), 1.0)]).fit(data)
    np.testing.assert_allclose(hybrid.score_items(0), [2.0, 2.0, 3.0, 3.0], err_msg="0.75*a + 0.25*b")


def test_hybrid_rejects_bad_weights():
    with pytest.raises(ValueError):
        HybridRecommender([])
    with pytest.raises(ValueError):
        HybridRecommender([(FixedScores([1.0]), 0.0)])
    with pytest.raises(ValueError):
        HybridRecommender([(FixedScores([1.0]), -1.0), (FixedScores([1.0]), 2.0)])
