"""Configuration schemas for Phase 6 Evidence Fusion and Candidate Decision Engine."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class EvidenceWeightsConfig(BaseModel):
    """Normalized weighting profile across multimodal evidence channels. Weights must sum to 1.0."""
    protein_ai_weight: float = 0.25
    uncertainty_quality_weight: float = 0.15
    mechanism_proximity_weight: float = 0.20
    chemistry_evidence_weight: float = 0.15
    quantum_evidence_weight: float = 0.15
    diversity_weight: float = 0.10

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "EvidenceWeightsConfig":
        total = (
            self.protein_ai_weight
            + self.uncertainty_quality_weight
            + self.mechanism_proximity_weight
            + self.chemistry_evidence_weight
            + self.quantum_evidence_weight
            + self.diversity_weight
        )
        if abs(total - 1.0) > 1e-4:
            raise ValueError(
                f"Evidence weights must sum to 1.0, got sum = {total:.6f} "
                f"(ai={self.protein_ai_weight}, unc={self.uncertainty_quality_weight}, "
                f"mech={self.mechanism_proximity_weight}, chem={self.chemistry_evidence_weight}, "
                f"qm={self.quantum_evidence_weight}, div={self.diversity_weight})"
            )
        return self


class DecisionThresholdsConfig(BaseModel):
    """Configurable numerical boundaries for candidate triage status classification."""
    prioritize_min_score: float = 0.70
    prioritize_min_coverage: float = 0.60
    promising_min_score: float = 0.50
    insufficient_evidence_max_coverage: float = 0.40
    low_priority_max_score: float = 0.40

    # Uncertainty classification thresholds
    uncertainty_low_threshold: float = 0.30
    uncertainty_high_threshold: float = 0.70

    # Quantum VQE vs CASCI error thresholds (Hartree)
    quantum_excellent_error_ha: float = 0.010  # ~6.27 kcal/mol
    quantum_acceptable_error_ha: float = 0.050


class FusionConfig(BaseModel):
    """Unified configuration for Phase 6 Evidence Fusion & Decision Engine."""
    weights: EvidenceWeightsConfig = Field(default_factory=EvidenceWeightsConfig)
    thresholds: DecisionThresholdsConfig = Field(default_factory=DecisionThresholdsConfig)

    missing_evidence_policy: str = "renormalize_available"  # Options: 'renormalize_available', 'neutral_prior', 'strict_penalty'
    synthetic_data_policy: str = "preserve_provenance"  # Options: 'preserve_provenance', 'reject_synthetic'
    
    # Input file paths
    protein_ai_path: Path = Path("protein_ai/predictions.parquet")
    uncertainty_path: Path = Path("uncertainty/uncertainty.parquet")
    acquisition_path: Path = Path("acquisition/selected_candidates.parquet")
    chemistry_path: Path = Path("chemistry/chem_results.parquet")
    quantum_path: Path = Path("quantum/quantum_results.parquet")

    # Output file paths
    output_results_parquet: Path = Path("fusion/fusion_results.parquet")
    output_evidence_matrix_parquet: Path = Path("fusion/evidence_matrix.parquet")
    output_manifest_json: Path = Path("fusion/fusion_manifest.json")
    output_explanations_json: Path = Path("fusion/candidate_explanations.json")
