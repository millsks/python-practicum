# Project 8: Movie Recommender

Part 8 (Machine Learning) graded project. Full brief with diagrams, rubric, and hints:
`docs/projects/p08-recommender.html` (`pixi run serve`).

## Scenario

You have joined **Reelhouse**, a small streaming service with a few hundred subscribers and a few hundred films.
The home page shows the same "Top 10" to everyone, and engagement is flat. Your job is to build the recommendation
engine: learn from star ratings (1 to 5) which films each subscriber is likely to enjoy, prove offline that it beats
the Top 10 list, and expose a simple `recommend(user_id, k)` API the web team can call.

Real ratings are private, so the package ships a deterministic synthetic generator. Every user and film has a
hidden 3-dimensional "taste" vector; ratings come from how well those tastes line up, plus user and film biases and
noise. Genres are derived from the same hidden tastes. A model that discovers the hidden structure will clearly beat
a popularity list; one that does not, won't.

## Getting started

```bash
pixi run start p08        # copies starter/ to work/p08_recommender/
pixi run grade p08        # runs the tests against your work/ copy
pixi run python -m recommender   # from work/p08_recommender/: prints the model comparison table
```

The starter contains the full public API with type hints and docstrings. Function bodies raise
`NotImplementedError` and carry `# TODO` comments. `generate_ratings`, `generate_items`, and the `Recommender`
base class are provided complete.

## Package layout

| Module | What it holds |
|---|---|
| `data.py` | `generate_ratings`, `generate_items`, `load_ratings_csv`, `RatingMatrix`, `build_matrix` |
| `base.py` | `Recommender` abstract base class (`fit`, `score_items`, `predict`, `predict_many`) |
| `baseline.py` | `bayesian_average`, `PopularityRecommender` |
| `neighbors.py` | `cosine_similarity`, `top_k_mask`, `ItemKNN`, `UserKNN` |
| `mf.py` | `rmse`, `MatrixFactorization` (biased MF trained with SGD) |
| `content.py` | `genre_matrix`, `ContentRecommender`, `HybridRecommender` |
| `evaluate.py` | `train_test_split_by_user`, `top_k`, `precision_at_k`, `recall_at_k`, `coverage`, `evaluate`, `compare_models`, `format_table` |
| `api.py` | `Recommendation`, `RecommenderService.recommend(user_id, k, exclude_seen=True)`, `main()` |

## Milestones

1. **Data.** Load ratings (CSV or generator) into a `scipy.sparse.csr_matrix` with sorted user/item id mappings.
   Reject duplicates and non-positive ratings (0 means "unrated" in the sparse matrix). Support cold items.
2. **Popularity baseline.** Rank items by a Bayesian average `(C*m + sum) / (C + n)` so one 5-star rating does not
   beat forty 4.5-star ratings.
3. **Neighborhood CF.** Item-item cosine similarity and user-user kNN, both predicting
   `mean + weighted average of neighbors' deviations`. Cold items and users fall back to a mean.
4. **Matrix factorization.** `r ~ mu + b_u + b_i + p_u . q_i`, SGD with L2 regularization, clipped predictions,
   training (and optional validation) RMSE recorded per epoch in `history_`.
5. **Content and hybrid.** One-hot genre vectors, a content model that can score never-rated films, and a weighted
   blend of any models.
6. **Evaluation.** Per-user hold-out split, RMSE, precision@k, recall@k, catalogue coverage, and a Markdown
   comparison table.
7. **API.** `RecommenderService(model).fit(data).recommend(user_id, k=10, exclude_seen=True)`, with a popularity
   fallback for unknown users.

## Grading

51 tests in `tests/`: small hand-computable matrices for every formula, plus a statistical check that matrix
factorization beats the popularity baseline by at least 0.1 RMSE on the synthetic data.

## Stretch goals

- Alternating least squares (ALS) as a second `MatrixFactorization` trainer; compare convergence with SGD.
- Implicit feedback: treat "watched" as a signal and optimize a ranking loss (BPR).
- Diversity and novelty metrics; re-rank results to trade a little precision for more coverage.
- Tune the hybrid weights on a validation split instead of guessing them.
- Wrap `RecommenderService` in a FastAPI endpoint (`pixi add fastapi uvicorn`).
