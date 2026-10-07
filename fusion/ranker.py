"""Deterministic candidate ranker with multi-tier tie-breaking for PETase variant triage."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd

from fusion.confidence import ConfidenceClassifier, DecisionClassification
from fusion.config import FusionConfig
from fusion.evidence import CandidateEvidenceProfile
from fusion.explanations import CandidateExplanation, ExplanationEngine
from fusion.scoring import CompositeScorer, FusionScoreResult


@dataclass
class RankedCandidate:
    """Complete triage record for a ranked PETase candidate."""
    rank: int
    candidate_id: str
    mutations: str
    parent_enzyme: str
    fusion_score: float
    decision_status: str
    confidence_label: str
    uncertainty_flag: str
    evidence_coverage_score: float
    available_evidence_count: int
    missing_evidence_count: int

    # Channel scores
    protein_ai_score: float
    uncertainty_quality_score: float
    mechanism_proximity_score: float
    chemistry_score: float
    quantum_score: float
    diversity_score: float

    # Availability flags
    protein_ai_available: bool
    uncertainty_available: bool
    mechanism_available: bool
    chemistry_available: bool
    quantum_available: bool
    diversity_available: bool

    # Backend and provenance metadata
    quantum_backend_type: str
    integral_backend: str
    vqe_casci_error: Optional[float]
    synthetic_data_present: bool

    # Structured explanation
    explanation: CandidateExplanation
    profile: CandidateEvidenceProfile
    score_result: FusionScoreResult
    classification: DecisionClassification


class CandidateRanker:
    """Executes deterministic ranking, scoring, classification, and explanation generation."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.scorer = CompositeScorer(self.config)
        self.classifier = ConfidenceClassifier(self.config)
        self.explanation_engine = ExplanationEngine()

    def rank_candidates(
        self, profiles: List[CandidateEvidenceProfile]
    ) -> List[RankedCandidate]:
        """Scores, classifies, tie-breaks, and deterministically ranks all candidate profiles."""
        if not profiles:
            return []

        # 1. Compute preliminary scores and classifications
        scored_items = []
        for profile in profiles:
            score_res = self.scorer.score_candidate(profile)
            classification = self.classifier.classify(profile, score_res)
            scored_items.append((profile, score_res, classification))

        # 2. Deterministic sort key:
        # - fusion_score (descending)
        # - evidence_coverage_score (descending)
        # - uncertainty_quality_score (descending, meaning lower uncertainty)
        # - mechanism_proximity_score (descending)
        # - candidate_id (ascending string)
        def sort_key(item):
            prof, sc, _ = item
            return (
                -sc.fusion_score,
                -sc.evidence_coverage_score,
                -prof.uncertainty_quality_score,
                -prof.mechanism_proximity_score,
                str(prof.candidate_id),
            )

        sorted_items = sorted(scored_items, key=sort_key)

        # 3. Build final RankedCandidate list with 1-indexed ranks and explanations
        ranked_candidates: List[RankedCandidate] = []
        for rank_idx, (prof, sc, cls) in enumerate(sorted_items, start=1):
            explanation = self.explanation_engine.generate_explanation(
                profile=prof,
                score_res=sc,
                classification=cls,
                rank=rank_idx,
            )

            ranked_candidates.append(
                RankedCandidate(
                    rank=rank_idx,
                    candidate_id=prof.candidate_id,
                    mutations=prof.mutations,
                    parent_enzyme=prof.parent_enzyme,
                    fusion_score=sc.fusion_score,
                    decision_status=cls.decision_status,
                    confidence_label=cls.confidence_label,
                    uncertainty_flag=cls.uncertainty_flag,
                    evidence_coverage_score=sc.evidence_coverage_score,
                    available_evidence_count=sc.available_evidence_count,
                    missing_evidence_count=sc.missing_evidence_count,
                    protein_ai_score=prof.protein_ai_score,
                    uncertainty_quality_score=prof.uncertainty_quality_score,
                    mechanism_proximity_score=prof.mechanism_proximity_score,
                    chemistry_score=prof.chemistry_score,
                    quantum_score=prof.quantum_score,
                    diversity_score=prof.diversity_score,
                    protein_ai_available=prof.protein_ai_feature.available,
                    uncertainty_available=prof.uncertainty_feature.available,
                    mechanism_available=prof.mechanism_feature.available,
                    chemistry_available=prof.chemistry_feature.available,
                    quantum_available=prof.quantum_feature.available,
                    diversity_available=prof.diversity_feature.available,
                    quantum_backend_type=prof.quantum_backend_type,
                    integral_backend=prof.integral_backend,
                    vqe_casci_error=prof.vqe_casci_error,
                    synthetic_data_present=prof.synthetic_data_present,
                    explanation=explanation,
                    profile=prof,
                    score_result=sc,
                    classification=cls,
                )
            )

        return ranked_candidates
