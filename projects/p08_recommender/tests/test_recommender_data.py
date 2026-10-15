"""Milestone 1: synthetic data, CSV loading, and the sparse rating matrix."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from recommender.data import GENRES, build_matrix, generate_items, generate_ratings, load_ratings_csv
from scipy.sparse import csr_matrix


def tiny_ratings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": ["bob", "ann", "ann", "cat", "bob"],
            "item_id": ["m2", "m1", "m2", "m3", "m1"],
            "rating": [3.0, 5.0, 4.0, 2.0, 1.0],
        }
    )


def test_generate_ratings_columns_and_range():
    df = generate_ratings(20, 30, seed=1)
    assert list(df.columns) == ["user_id", "item_id", "rating"], "columns must be user_id, item_id, rating"
    assert df["rating"].between(1, 5).all(), "ratings must be in 1..5"
    assert (df["rating"] == df["rating"].round()).all(), "synthetic ratings are whole stars"


def test_generate_ratings_is_deterministic():
    a = generate_ratings(15, 25, seed=3)
    b = generate_ratings(15, 25, seed=3)
    pd.testing.assert_frame_equal(a, b, obj="same seed must give the same ratings")


def test_generate_ratings_depends_on_seed():
    a = generate_ratings(15, 25, seed=3)
    b = generate_ratings(15, 25, seed=4)
    assert not a.equals(b), "different seeds should give different ratings"


def test_generate_ratings_each_user_rates_at_least_five_without_duplicates():
    df = generate_ratings(12, 40, seed=0, density=0.05)
    counts = df.groupby("user_id").size()
    assert len(counts) == 12, "every user should appear"
    assert (counts >= 5).all(), "each user rates at least 5 items"
    assert not df.duplicated(["user_id", "item_id"]).any(), "a user rates an item at most once"


def test_generate_ratings_rejects_bad_sizes():
    with pytest.raises(ValueError):
        generate_ratings(0, 10)
    with pytest.raises(ValueError):
        generate_ratings(5, 10, density=0.0)


def test_generate_items_has_valid_genres_for_every_item():
    items = generate_items(30, seed=2)
    assert len(items) == 30 and items["item_id"].is_unique, "one row per item"
    for genres in items["genres"]:
        parts = genres.split("|")
        assert parts and all(g in GENRES for g in parts), f"unknown genre in {genres!r}"


def test_generate_items_ids_match_ratings():
    ratings = generate_ratings(10, 20, seed=5)
    items = generate_items(20, seed=5)
    assert set(ratings["item_id"]) <= set(items["item_id"]), "every rated item must have metadata"


def test_load_ratings_csv_round_trip(tmp_path: Path):
    path = tmp_path / "ratings.csv"
    tiny_ratings().assign(extra=1).to_csv(path, index=False)
    loaded = load_ratings_csv(path)
    assert list(loaded.columns) == ["user_id", "item_id", "rating"], "extra columns are dropped"
    assert loaded["rating"].dtype == float, "ratings are floats"
    assert loaded["user_id"].tolist() == ["bob", "ann", "ann", "cat", "bob"], "ids stay strings in order"


def test_load_ratings_csv_missing_column(tmp_path: Path):
    path = tmp_path / "bad.csv"
    path.write_text("user_id,rating\nu1,4\n", encoding="utf-8")
    with pytest.raises(ValueError, match="item_id"):
        load_ratings_csv(path)


def test_build_matrix_shape_and_sorted_mappings():
    data = build_matrix(tiny_ratings())
    assert isinstance(data.matrix, csr_matrix), "matrix must be a scipy csr_matrix"
    assert data.matrix.shape == (3, 3), "3 users x 3 items"
    assert data.user_ids == ("ann", "bob", "cat"), "users are indexed in sorted order"
    assert data.item_ids == ("m1", "m2", "m3"), "items are indexed in sorted order"
    assert data.user_index["cat"] == 2 and data.item_index["m2"] == 1, "index maps invert the id tuples"


def test_build_matrix_values():
    data = build_matrix(tiny_ratings())
    dense = data.matrix.toarray()
    expected = np.array([[5.0, 4.0, 0.0], [1.0, 3.0, 0.0], [0.0, 0.0, 2.0]])
    np.testing.assert_array_equal(dense, expected, err_msg="ratings land at [user, item]; 0 means unrated")
    assert data.nnz == 5, "five stored ratings"
    assert data.global_mean == pytest.approx(3.0), "mean of 5,4,1,3,2 is 3"


def test_build_matrix_user_ratings_and_counts():
    data = build_matrix(tiny_ratings())
    items, ratings = data.user_ratings(1)
    assert items.tolist() == [0, 1] and ratings.tolist() == [1.0, 3.0], "bob rated m1=1 and m2=3"
    assert data.counts_per_item().tolist() == [2, 2, 1], "ratings per item"


def test_build_matrix_with_cold_items():
    data = build_matrix(tiny_ratings(), item_ids=["m1", "m2", "m3", "m9"])
    assert data.n_items == 4, "catalogue items without ratings still get a column"
    assert data.counts_per_item()[data.item_index["m9"]] == 0, "the cold item has no ratings"


def test_build_matrix_rejects_duplicates_and_bad_values():
    dup = pd.concat([tiny_ratings(), tiny_ratings().head(1)])
    with pytest.raises(ValueError, match="duplicate"):
        build_matrix(dup)
    zero = tiny_ratings().assign(rating=[3.0, 0.0, 4.0, 2.0, 1.0])
    with pytest.raises(ValueError):
        build_matrix(zero)
    with pytest.raises(ValueError):
        build_matrix(tiny_ratings(), item_ids=["m1", "m2"])
