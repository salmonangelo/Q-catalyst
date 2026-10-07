"""Configuration schema for Protein-AI representations, predictors, and uncertainty estimation."""

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ESMConfig(BaseModel):
    """Configuration for ESM protein language models."""
    model_name: str = "facebook/esm2_t6_8M_UR50D"  # Lightweight 8M parameter default for CPU efficiency
    fallback_model_name: str = "heuristic_esm_mock"  # Offline fallback for tests/environments without weights
    device: str = "cpu"
    batch_size: int = 8
    max_sequence_length: int = 1024
    embedding_layer: int = -1  # Final hidden representation
    use_cache: bool = True
    cache_dir: Path = Path("protein_ai/cache")


class PredictorConfig(BaseModel):
    """Configuration for downstream supervised fitness predictors."""
    model_type: str = "ridge"  # Options: 'ridge', 'gradient_boosting', 'random_forest', 'xgboost'
    alpha: float = 1.0  # L2 regularization for ridge
    n_estimators: int = 100  # For tree-based models
    max_depth: int = 4
    random_seed: int = 42
    target_column: str = "activity_rel_to_parent"
    secondary_target_column: Optional[str] = "Tm_C"
    normalize_features: bool = True
    artifacts_dir: Path = Path("artifacts/protein_ai")


class UncertaintyConfig(BaseModel):
    """Configuration for multi-component uncertainty and OOD estimation."""
    ensemble_size: int = 10
    ensemble_subsample_ratio: float = 0.8
    ood_k_neighbors: int = 5
    ood_metric: str = "euclidean"  # 'euclidean', 'mahalanobis', 'cosine'
    conformal_alpha: float = 0.10  # 90% confidence level (1 - alpha)
    weight_ensemble: float = 0.40
    weight_ood: float = 0.35
    weight_conformal: float = 0.25
    uncertainty_output_path: Path = Path("uncertainty/uncertainty.parquet")
    gate0_report_json: Path = Path("uncertainty/gate0_report.json")
    gate0_report_md: Path = Path("uncertainty/GATE0_REPORT.md")


class ProteinAIConfig(BaseModel):
    """Unified configuration for Phase 2."""
    esm: ESMConfig = Field(default_factory=ESMConfig)
    predictor: PredictorConfig = Field(default_factory=PredictorConfig)
    uncertainty: UncertaintyConfig = Field(default_factory=UncertaintyConfig)
