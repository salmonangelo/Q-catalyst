"""Composite multi-objective evidence scoring and missing-evidence policy engine."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np

from fusion.config import EvidenceWeightsConfig, FusionConfig
from fusion.evidence import CandidateEvidenceProfile


@dataclass
class FusionScoreResult:
    """Individual candidate multi-channel composite fusion evaluation."""
    candidate_id: str
    fusion_score: float  # [0, 1]
    evidence_coverage_score: float  # [0, 1]
    available_evidence_count: int
    missing_evidence_count: int
    weights_applied: Dict[str, float] = field(default_factory=dict)
    channel_scores: Dict[str, float] = field(default_factory=dict)


class CompositeScorer:
    """Calculates weighted multi-channel evidence scores under configurable missing-data policies."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()

    def score_candidate(self, profile: CandidateEvidenceProfile) -> FusionScoreResult:
        """Calculates the composite fusion score for a single candidate profile."""
        weights = self.config.weights
        policy = self.config.missing_evidence_policy

        channel_scores = {
            "protein_ai": profile.protein_ai_score,
            "uncertainty": profile.uncertainty_quality_score,
            "mechanism": profile.mechanism_proximity_score,
            "chemistry": profile.chemistry_score,
            "quantum": profile.quantum_score,
            "diversity": profile.diversity_score,
        }

        channel_avail = {
            "protein_ai": profile.protein_ai_feature.available,
            "uncertainty": profile.uncertainty_feature.available,
            "mechanism": profile.mechanism_feature.available,
            "chemistry": profile.chemistry_feature.available,
            "quantum": profile.quantum_feature.available,
            "diversity": profile.diversity_feature.available,
        }

        base_weights = {
            "protein_ai": weights.protein_ai_weight,
            "uncertainty": weights.uncertainty_quality_weight,
            "mechanism": weights.mechanism_proximity_weight,
            "chemistry": weights.chemistry_evidence_weight,
            "quantum": weights.quantum_evidence_weight,
            "diversity": weights.diversity_weight,
        }

        applied_weights: Dict[str, float] = {}

        if policy == "renormalize_available":
            # Sum weights of available channels
            avail_weight_sum = sum(base_weights[ch] for ch, is_av in channel_avail.items() if is_av)
            if avail_weight_sum > 0:
                for ch in base_weights:
                    if channel_avail[ch]:
                        applied_weights[ch] = base_weights[ch] / avail_weight_sum
                    else:
                        applied_weights[ch] = 0.0
            else:
                applied_weights = {ch: 1.0 / len(base_weights) for ch in base_weights}
        else:
            # Fixed base weights
            applied_weights = dict(base_weights)

        # Compute weighted linear combination
        composite_score = sum(applied_weights[ch] * channel_scores[ch] for ch in base_weights)
        composite_score = float(np.clip(composite_score, 0.0, 1.0))

        avail_count = len(profile.available_channels)
        missing_count = len(profile.missing_channels)
        coverage_score = float(avail_count / 6.0)

        return FusionScoreResult(
            candidate_id=profile.candidate_id,
            fusion_score=composite_score,
            evidence_coverage_score=coverage_score,
            available_evidence_count=avail_count,
            missing_evidence_count=missing_count,
            weights_applied=applied_weights,
            channel_scores=channel_scores,
        )
