"""A small movie recommender: baselines, neighborhood CF, matrix factorization, content, and evaluation."""

from recommender.api import Recommendation, RecommenderService
from recommender.base import NotFittedError, Recommender
from recommender.baseline import PopularityRecommender, bayesian_average
from recommender.content import ContentRecommender, HybridRecommender, genre_matrix
from recommender.data import RatingMatrix, build_matrix, generate_items, generate_ratings, load_ratings_csv
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
from recommender.mf import MatrixFactorization, rmse
from recommender.neighbors import ItemKNN, UserKNN, cosine_similarity, top_k_mask

__all__ = [
    "ContentRecommender",
    "EvaluationResult",
    "HybridRecommender",
    "ItemKNN",
    "MatrixFactorization",
    "NotFittedError",
    "PopularityRecommender",
    "RatingMatrix",
    "Recommendation",
    "Recommender",
    "RecommenderService",
    "UserKNN",
    "bayesian_average",
    "build_matrix",
    "compare_models",
    "cosine_similarity",
    "coverage",
    "evaluate",
    "format_table",
    "generate_items",
    "generate_ratings",
    "genre_matrix",
    "load_ratings_csv",
    "precision_at_k",
    "recall_at_k",
    "rmse",
    "top_k",
    "top_k_mask",
    "train_test_split_by_user",
]
