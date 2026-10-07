"""Multimodal evidence normalization with full provenance and metadata tracking."""

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class NormalizedFeature:
    """Individual normalized evidence element with rigorous traceability metadata."""
    candidate_id: str
    evidence_name: str
    raw_value: Optional[float]
    normalized_value: float  # Guaranteed in [0.0, 1.0]
    normalization_method: str
    source_module: str
    source_artifact: str
    source_column: str
    available: bool
    data_quality_flag: str
    synthetic: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceNormalizer:
    """Normalizes raw heterogeneous multimodal signals into standard [0, 1] evidence channels."""

    def __init__(self):
        pass

    def normalize_protein_ai(
        self,
        candidate_id: str,
        raw_prediction: Optional[float],
        min_val: float = 0.0,
        max_val: float = 1.0,
        source_artifact: str = "protein_ai/predictions.parquet",
        data_quality_flag: str = "COMPUTED_SEQUENCE_AI_PREDICTION",
        synthetic: bool = False,
    ) -> NormalizedFeature:
        """Normalizes sequence-based Protein-AI fitness prediction."""
        if raw_prediction is None or np.isnan(raw_prediction):
            return NormalizedFeature(
                candidate_id=candidate_id,
                evidence_name="protein_ai_score",
                raw_value=None,
                normalized_value=0.5,
                normalization_method="missing_neutral_prior",
                source_module="protein_ai",
                source_artifact=source_artifact,
                source_column="prediction",
                available=False,
                data_quality_flag=data_quality_flag,
                synthetic=synthetic,
            )

        # Min-max bounded scaling with clipping
        span = max(1e-5, max_val - min_val)
        norm_val = float(np.clip((raw_prediction - min_val) / span, 0.0, 1.0))

        return NormalizedFeature(
            candidate_id=candidate_id,
            evidence_name="protein_ai_score",
            raw_value=float(raw_prediction),
            normalized_value=norm_val,
            normalization_method=f"bounded_min_max_[{min_val}:{max_val}]",
            source_module="protein_ai",
            source_artifact=source_artifact,
            source_column="prediction",
            available=True,
            data_quality_flag=data_quality_flag,
            synthetic=synthetic,
        )

    def normalize_uncertainty_quality(
        self,
        candidate_id: str,
        raw_uncertainty: Optional[float],
        source_artifact: str = "uncertainty/uncertainty.parquet",
        data_quality_flag: str = "CALIBRATED_COMPOSITE_UNCERTAINTY",
        synthetic: bool = False,
    ) -> NormalizedFeature:
        """Normalizes uncertainty into a quality score where lower uncertainty gives higher score."""
        if raw_uncertainty is None or np.isnan(raw_uncertainty):
            return NormalizedFeature(
                candidate_id=candidate_id,
                evidence_name="uncertainty_quality",
                raw_value=None,
                normalized_value=0.5,
                normalization_method="missing_neutral_prior",
                source_module="uncertainty",
                source_artifact=source_artifact,
                source_column="uncertainty_score",
                available=False,
                data_quality_flag=data_quality_flag,
                synthetic=synthetic,
            )

        # Exponential decay: S_unc = exp(-2.0 * U) -> U=0 => 1.0, U=0.5 => 0.368, U=1.0 => 0.135
        u_clipped = float(np.clip(raw_uncertainty, 0.0, 3.0))
        norm_val = float(np.exp(-1.5 * u_clipped))

        return NormalizedFeature(
            candidate_id=candidate_id,
            evidence_name="uncertainty_quality",
            raw_value=float(raw_uncertainty),
            normalized_value=norm_val,
            normalization_method="exponential_decay_quality_exp(-1.5*u)",
            source_module="uncertainty",
            source_artifact=source_artifact,
            source_column="uncertainty_score",
            available=True,
            data_quality_flag=data_quality_flag,
            synthetic=synthetic,
        )

    def normalize_mechanism_proximity(
        self,
        candidate_id: str,
        raw_proximity: Optional[float] = None,
        min_distance_angstrom: Optional[float] = None,
        source_artifact: str = "acquisition/selected_candidates.parquet",
        data_quality_flag: str = "3D_ACTIVE_SITE_PROXIMITY_5XJH",
        synthetic: bool = False,
    ) -> NormalizedFeature:
        """Normalizes active-site structural proximity signal."""
        if raw_proximity is not None and not np.isnan(raw_proximity):
            norm_val = float(np.clip(raw_proximity, 0.0, 1.0))
            raw_val = float(raw_proximity)
            method = "acquisition_proximity_clip_[0:1]"
        elif min_distance_angstrom is not None and not np.isnan(min_distance_angstrom):
            # Smooth exponential decay: d=0 A => 1.0, d=8 A => 0.368
            raw_val = float(min_distance_angstrom)
            norm_val = float(np.exp(-raw_val / 8.0))
            method = "exponential_distance_decay_exp(-d/8.0A)"
        else:
            return NormalizedFeature(
                candidate_id=candidate_id,
                evidence_name="mechanism_proximity",
                raw_value=None,
                normalized_value=0.5,
                normalization_method="missing_neutral_prior",
                source_module="acquisition",
                source_artifact=source_artifact,
                source_column="proximity_score",
                available=False,
                data_quality_flag=data_quality_flag,
                synthetic=synthetic,
            )

        return NormalizedFeature(
            candidate_id=candidate_id,
            evidence_name="mechanism_proximity",
            raw_value=raw_val,
            normalized_value=norm_val,
            normalization_method=method,
            source_module="acquisition",
            source_artifact=source_artifact,
            source_column="active_site_proximity",
            available=True,
            data_quality_flag=data_quality_flag,
            synthetic=synthetic,
        )

    def normalize_chemistry_evidence(
        self,
        candidate_id: str,
        geometry_status: Optional[str] = "valid",
        scf_converged: Optional[bool] = True,
        delta_energy: Optional[float] = None,
        calculation_status: Optional[str] = "COMPLETED",
        source_artifact: str = "chemistry/chem_results.parquet",
        data_quality_flag: str = "CLASSICAL_ELECTRONIC_STRUCTURE",
        synthetic: bool = False,
    ) -> NormalizedFeature:
        """Normalizes classical chemistry validity, convergence, and energetic stability."""
        if calculation_status != "COMPLETED" or geometry_status == "invalid":
            return NormalizedFeature(
                candidate_id=candidate_id,
                evidence_name="chemistry_evidence",
                raw_value=0.0,
                normalized_value=0.0,
                normalization_method="failed_calculation_penalty",
                source_module="chemistry",
                source_artifact=source_artifact,
                source_column="calculation_status",
                available=False,
                data_quality_flag=data_quality_flag,
                synthetic=synthetic,
            )

        score = 0.5  # Base score for valid geometry and completed calculation
        if geometry_status == "valid":
            score += 0.25
        elif geometry_status == "warning":
            score += 0.10

        if scf_converged:
            score += 0.25

        # Energy bonus/penalty if delta_energy relative to WT is provided
        if delta_energy is not None and not np.isnan(delta_energy):
            # Negative delta_energy is stabilizing; positive is destabilizing
            # 1 Hartree is very large, so scale by ~0.05 Ha (~30 kcal/mol)
            stab_adjustment = -0.15 * float(np.tanh(delta_energy / 0.05))
            score = float(np.clip(score + stab_adjustment, 0.0, 1.0))

        return NormalizedFeature(
            candidate_id=candidate_id,
            evidence_name="chemistry_evidence",
            raw_value=float(delta_energy) if delta_energy is not None else 0.0,
            normalized_value=score,
            normalization_method="geometry_validity_+_scf_convergence_+_delta_energy_tanh",
            source_module="chemistry",
            source_artifact=source_artifact,
            source_column="geometry_status_and_delta_energy",
            available=True,
            data_quality_flag=data_quality_flag,
            synthetic=synthetic,
        )

    def normalize_quantum_evidence(
        self,
        candidate_id: str,
        vqe_casci_error: Optional[float],
        vqe_converged: bool = True,
        source_artifact: str = "quantum/quantum_results.parquet",
        data_quality_flag: str = "SIMULATED_QUANTUM_VQE_EXPERIMENT",
        synthetic: bool = False,
    ) -> NormalizedFeature:
        """Normalizes quantum VQE vs CASCI exact agreement into [0, 1]."""
        if vqe_casci_error is None or np.isnan(vqe_casci_error):
            return NormalizedFeature(
                candidate_id=candidate_id,
                evidence_name="quantum_evidence",
                raw_value=None,
                normalized_value=0.5,
                normalization_method="missing_neutral_prior",
                source_module="quantum",
                source_artifact=source_artifact,
                source_column="vqe_absolute_error",
                available=False,
                data_quality_flag=data_quality_flag,
                synthetic=synthetic,
            )

        err = float(abs(vqe_casci_error))
        # Smooth exponential agreement: err=0 => 1.0, err=0.01 Ha => 0.74, err=0.05 Ha => 0.22
        norm_val = float(np.exp(-30.0 * err))
        if not vqe_converged:
            norm_val *= 0.5

        return NormalizedFeature(
            candidate_id=candidate_id,
            evidence_name="quantum_evidence",
            raw_value=err,
            normalized_value=norm_val,
            normalization_method="exponential_vqe_casci_agreement_exp(-30*err)",
            source_module="quantum",
            source_artifact=source_artifact,
            source_column="vqe_absolute_error",
            available=True,
            data_quality_flag=data_quality_flag,
            synthetic=synthetic,
        )

    def normalize_diversity(
        self,
        candidate_id: str,
        raw_diversity: Optional[float],
        source_artifact: str = "acquisition/selected_candidates.parquet",
        data_quality_flag: str = "SEQUENCE_EMBEDDING_DIVERSITY",
        synthetic: bool = False,
    ) -> NormalizedFeature:
        """Normalizes acquisition diversity score."""
        if raw_diversity is None or np.isnan(raw_diversity):
            return NormalizedFeature(
                candidate_id=candidate_id,
                evidence_name="diversity",
                raw_value=None,
                normalized_value=0.5,
                normalization_method="missing_neutral_prior",
                source_module="acquisition",
                source_artifact=source_artifact,
                source_column="diversity_score",
                available=False,
                data_quality_flag=data_quality_flag,
                synthetic=synthetic,
            )

        norm_val = float(np.clip(raw_diversity, 0.0, 1.0))
        return NormalizedFeature(
            candidate_id=candidate_id,
            evidence_name="diversity",
            raw_value=float(raw_diversity),
            normalized_value=norm_val,
            normalization_method="bounded_clipping_[0:1]",
            source_module="acquisition",
            source_artifact=source_artifact,
            source_column="diversity_score",
            available=True,
            data_quality_flag=data_quality_flag,
            synthetic=synthetic,
        )
