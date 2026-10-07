"""Protein AI module for ESM representation, zero-shot mutation scoring, and fitness prediction."""

from .config import ESMConfig, PredictorConfig, ProteinAIConfig, UncertaintyConfig
from .embeddings import EmbeddingExtractor
from .esm import ESMModelWrapper, get_esm_model
from .features import FeaturePipeline
from .inference import run_protein_ai_pipeline
from .mutation_scoring import MutationScoreResult, MutationScorer
from .outputs import PREDICTION_COLUMNS, enforce_predictions_schema, save_predictions_parquet
from .predictors import FitnessPredictor
from .utils import compute_regression_metrics, create_synthetic_variant_dataset

__all__ = [
    "ESMConfig",
    "PredictorConfig",
    "UncertaintyConfig",
    "ProteinAIConfig",
    "ESMModelWrapper",
    "get_esm_model",
    "EmbeddingExtractor",
    "MutationScoreResult",
    "MutationScorer",
    "FeaturePipeline",
    "FitnessPredictor",
    "PREDICTION_COLUMNS",
    "enforce_predictions_schema",
    "save_predictions_parquet",
    "run_protein_ai_pipeline",
    "compute_regression_metrics",
    "create_synthetic_variant_dataset",
]
