"""Configuration schema for Phase 3 Smart Acquisition Gate."""

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class ProximityConfig(BaseModel):
    """Configuration for structure mapping and active-site proximity scoring."""
    reference_pdb_path: Path = Path("data/structures/5xjh.pdb")
    reference_chain_id: str = "A"
    reference_parent: str = "IsPETase"
    # Catalytic triad (Ser160, Asp206, His237), Oxyanion hole (Tyr87, Met161), Substrate pocket (Trp185, Trp159)
    active_site_residues: List[int] = Field(
        default_factory=lambda: [160, 206, 237, 87, 161, 185, 159]
    )
    decay_length_angstrom: float = 8.0  # Characteristic length scale d0 for exponential decay


class DiversityConfig(BaseModel):
    """Configuration for sequence diversity and redundancy minimization."""
    metric: str = "embedding_distance"  # 'embedding_distance' or 'mutation_jaccard'
    similarity_threshold: float = 0.85
    min_diversity_penalty: float = 0.0


class AcquisitionWeights(BaseModel):
    """Relative weighting parameters for acquisition scoring."""
    alpha_performance: float = 0.35
    beta_uncertainty: float = 0.25
    gamma_proximity: float = 0.25
    delta_diversity: float = 0.15
    lambda_cost: float = 0.05


class AcquisitionConfig(BaseModel):
    """Unified configuration for Smart Acquisition Gate."""
    chemistry_budget: int = 10
    strategy: str = "mechanism_aware"  # 'mechanism_aware', 'performance_only', 'uncertainty_only', 'mechanism_aware_without_uncertainty', 'diversity_plus_performance'
    performance_quantile: Optional[float] = 0.50  # Keep top 50% predicted candidates before ranking
    performance_threshold: Optional[float] = None
    require_gate0_validation: bool = True  # If True and Gate-0 is weak/unvalidated, triggers fallback strategy
    random_seed: int = 42

    proximity: ProximityConfig = Field(default_factory=ProximityConfig)
    diversity: DiversityConfig = Field(default_factory=DiversityConfig)
    weights: AcquisitionWeights = Field(default_factory=AcquisitionWeights)

    output_jobs_json: Path = Path("acquisition/chem_jobs.json")
    output_candidates_parquet: Path = Path("acquisition/selected_candidates.parquet")
