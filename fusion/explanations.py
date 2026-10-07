"""Deterministic, rule-based explainability engine for fused candidate decisions."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from fusion.confidence import DecisionClassification
from fusion.evidence import CandidateEvidenceProfile
from fusion.scoring import FusionScoreResult


@dataclass
class CandidateExplanation:
    """Structured, deterministic explainability report for a prioritized enzyme candidate."""
    candidate_id: str
    rank: int
    decision_status: str
    confidence_label: str
    fusion_score: float
    summary: str
    positive_factors: List[str] = field(default_factory=list)
    negative_factors: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExplanationEngine:
    """Generates factual, deterministic explanations directly from structured multimodal evidence."""

    def __init__(self):
        pass

    def generate_explanation(
        self,
        profile: CandidateEvidenceProfile,
        score_res: FusionScoreResult,
        classification: DecisionClassification,
        rank: int,
    ) -> CandidateExplanation:
        """Constructs an explainable triage rationale for a single candidate."""
        positives: List[str] = []
        negatives: List[str] = []
        missing: List[str] = []
        limitations: List[str] = []

        # 1. Evaluate Protein-AI
        if profile.protein_ai_feature.available:
            if profile.protein_ai_score >= 0.70:
                positives.append(f"Strong protein sequence fitness score ({profile.protein_ai_score:.2f}).")
            elif profile.protein_ai_score <= 0.40:
                negatives.append(f"Low predicted sequence fitness ({profile.protein_ai_score:.2f}).")
        else:
            missing.append("Sequence AI fitness prediction was unavailable.")

        # 2. Evaluate Uncertainty
        if profile.uncertainty_feature.available:
            if classification.uncertainty_flag == "LOW":
                positives.append(f"Low predictive uncertainty ({classification.uncertainty_flag}).")
            elif classification.uncertainty_flag == "HIGH":
                negatives.append(f"High predictive uncertainty ({classification.uncertainty_flag}).")
        else:
            missing.append("Model uncertainty estimate was unavailable.")

        # 3. Evaluate Mechanism Proximity
        if profile.mechanism_feature.available:
            if profile.mechanism_proximity_score >= 0.70:
                positives.append(f"High catalytic active-site geometric proximity ({profile.mechanism_proximity_score:.2f}).")
            elif profile.mechanism_proximity_score <= 0.35:
                negatives.append(f"Distal to core catalytic active-site pocket ({profile.mechanism_proximity_score:.2f}).")
        else:
            missing.append("Active-site structural proximity was unavailable.")

        # 4. Evaluate Chemistry
        if profile.chemistry_feature.available:
            if profile.chemistry_score >= 0.70:
                positives.append("Valid active-site cluster geometry and converged classical electronic structure.")
            else:
                negatives.append("Sub-optimal classical chemistry validity or destabilizing active-site cluster.")
        else:
            missing.append("Classical chemistry electronic structure was not computed for this candidate.")

        # 5. Evaluate Quantum
        if profile.quantum_feature.available:
            if profile.vqe_casci_error is not None:
                if profile.vqe_casci_error < 0.015:
                    positives.append(f"Excellent VQE/CASCI quantum agreement (|ΔE| = {profile.vqe_casci_error:.4f} Ha).")
                elif profile.vqe_casci_error < 0.050:
                    positives.append(f"Acceptable VQE/CASCI quantum agreement (|ΔE| = {profile.vqe_casci_error:.4f} Ha).")
                else:
                    negatives.append(f"Elevated VQE variational error vs CASCI (|ΔE| = {profile.vqe_casci_error:.4f} Ha).")
        else:
            missing.append("Quantum simulation was not executed for this candidate.")

        # 6. Diversity
        if profile.diversity_feature.available and profile.diversity_score >= 0.70:
            positives.append("High mutational sequence diversity relative to other candidates.")

        # 7. Document Scientific Limitations
        limitations.append("This ranking represents computational triage recommendation, not experimental proof of enzyme kinetics.")
        if profile.quantum_backend_type and profile.quantum_backend_type.upper() == "SIMULATOR":
            limitations.append("Quantum evidence is derived from classical statevector simulation on simulator backend of a reduced (4e, 4o) active-space model (not quantum hardware).")
        if profile.integral_backend and profile.integral_backend.upper() == "CLASSICAL_FALLBACK":
            limitations.append("Active-space integrals were derived from physical-chemical model calculations rather than ab-initio PySCF.")
        if profile.synthetic_data_present:
            limitations.append("Candidate evaluation utilized synthetic test fixtures (PET-Gym benchmark data not present locally).")

        # Compose Summary
        pos_summary = ", ".join(positives[:2]) if positives else "moderate baseline metrics"
        neg_summary = f"; tempered by {negatives[0].lower()}" if negatives else ""
        summary = (
            f"Ranked #{rank} with composite fusion score {score_res.fusion_score:.2f} ({classification.decision_status}). "
            f"Supported by {pos_summary}{neg_summary}. Evidence coverage: {score_res.available_evidence_count}/6 channels."
        )

        return CandidateExplanation(
            candidate_id=profile.candidate_id,
            rank=rank,
            decision_status=classification.decision_status,
            confidence_label=classification.confidence_label,
            fusion_score=score_res.fusion_score,
            summary=summary,
            positive_factors=positives,
            negative_factors=negatives,
            missing_evidence=missing,
            limitations=limitations,
        )
