"""Unit tests for Phase 6 Multimodal Evidence Fusion and Decision Engine."""

import pytest
import numpy as np
import pandas as pd

from fusion.config import DecisionThresholdsConfig, EvidenceWeightsConfig, FusionConfig
from fusion.confidence import ConfidenceClassifier, DecisionClassification
from fusion.evidence import CandidateEvidenceProfile, EvidenceAggregator
from fusion.explanations import CandidateExplanation, ExplanationEngine
from fusion.normalize import EvidenceNormalizer, NormalizedFeature
from fusion.outputs import FusionOutputWriter
from fusion.ranker import CandidateRanker, RankedCandidate
from fusion.scoring import CompositeScorer, FusionScoreResult


def test_evidence_weights_validation():
    """Verify that EvidenceWeightsConfig strictly validates sum to 1.0."""
    # Valid weights
    cfg = EvidenceWeightsConfig(
        protein_ai_weight=0.25,
        uncertainty_quality_weight=0.15,
        mechanism_proximity_weight=0.20,
        chemistry_evidence_weight=0.15,
        quantum_evidence_weight=0.15,
        diversity_weight=0.10,
    )
    assert abs(cfg.protein_ai_weight + cfg.uncertainty_quality_weight + cfg.mechanism_proximity_weight +
               cfg.chemistry_evidence_weight + cfg.quantum_evidence_weight + cfg.diversity_weight - 1.0) < 1e-5

    # Invalid weights sum
    with pytest.raises(ValueError, match="Evidence weights must sum to 1.0"):
        EvidenceWeightsConfig(
            protein_ai_weight=0.50,
            uncertainty_quality_weight=0.50,
            mechanism_proximity_weight=0.20,
            chemistry_evidence_weight=0.15,
            quantum_evidence_weight=0.15,
            diversity_weight=0.10,
        )


def test_evidence_normalizer_channels():
    """Test normalization behavior across all 6 evidence channels."""
    normalizer = EvidenceNormalizer()

    # 1. Protein-AI
    feat_ai = normalizer.normalize_protein_ai("VAR_1", raw_prediction=0.85, synthetic=False)
    assert feat_ai.available is True
    assert 0.0 <= feat_ai.normalized_value <= 1.0
    assert feat_ai.evidence_name == "protein_ai_score"

    # Missing AI
    feat_ai_missing = normalizer.normalize_protein_ai("VAR_1", raw_prediction=None)
    assert feat_ai_missing.available is False
    assert feat_ai_missing.normalized_value == 0.5  # Neutral baseline for missing

    # 2. Uncertainty (Higher quality = lower uncertainty)
    feat_unc_low = normalizer.normalize_uncertainty_quality("VAR_1", raw_uncertainty=0.1)
    feat_unc_high = normalizer.normalize_uncertainty_quality("VAR_1", raw_uncertainty=0.9)
    assert feat_unc_low.normalized_value > feat_unc_high.normalized_value

    # 3. Mechanism proximity (Closer distance = higher score)
    feat_mech_close = normalizer.normalize_mechanism_proximity("VAR_1", min_distance_angstrom=3.5)
    feat_mech_far = normalizer.normalize_mechanism_proximity("VAR_1", min_distance_angstrom=18.0)
    assert feat_mech_close.normalized_value > feat_mech_far.normalized_value

    # 4. Chemistry evidence
    feat_chem_valid = normalizer.normalize_chemistry_evidence("VAR_1", geometry_status="valid", scf_converged=True)
    feat_chem_invalid = normalizer.normalize_chemistry_evidence("VAR_1", geometry_status="clash", scf_converged=False)
    assert feat_chem_valid.normalized_value > feat_chem_invalid.normalized_value

    # 5. Quantum evidence (Lower VQE-CASCI error = higher score)
    feat_qm_good = normalizer.normalize_quantum_evidence("VAR_1", vqe_casci_error=0.005)
    feat_qm_poor = normalizer.normalize_quantum_evidence("VAR_1", vqe_casci_error=0.150)
    assert feat_qm_good.normalized_value > feat_qm_poor.normalized_value

    # 6. Diversity
    feat_div = normalizer.normalize_diversity("VAR_1", raw_diversity=0.75)
    assert feat_div.normalized_value == 0.75


def test_composite_scorer_renormalization():
    """Verify missing-evidence renormalization policy in CompositeScorer."""
    config = FusionConfig(missing_evidence_policy="renormalize_available")
    scorer = CompositeScorer(config)
    normalizer = EvidenceNormalizer()

    # Create profile with 4 of 6 channels available
    p = CandidateEvidenceProfile(
        candidate_id="VAR_TEST",
        mutations="S160A",
        parent_enzyme="IsPETase",
        protein_ai_feature=normalizer.normalize_protein_ai("VAR_TEST", raw_prediction=0.90),
        uncertainty_feature=normalizer.normalize_uncertainty_quality("VAR_TEST", raw_uncertainty=0.10),
        mechanism_feature=normalizer.normalize_mechanism_proximity("VAR_TEST", min_distance_angstrom=4.0),
        chemistry_feature=normalizer.normalize_chemistry_evidence("VAR_TEST", calculation_status="MISSING"),  # unavailable
        quantum_feature=normalizer.normalize_quantum_evidence("VAR_TEST", vqe_casci_error=None),  # unavailable
        diversity_feature=normalizer.normalize_diversity("VAR_TEST", raw_diversity=0.80),
    )

    assert p.evidence_coverage_score == pytest.approx(4.0 / 6.0)
    assert len(p.available_channels) == 4
    assert len(p.missing_channels) == 2

    res = scorer.score_candidate(p)
    assert res.evidence_coverage_score == pytest.approx(4.0 / 6.0)
    assert sum(res.weights_applied.values()) == pytest.approx(1.0)
    assert res.weights_applied["chemistry"] == 0.0
    assert res.weights_applied["quantum"] == 0.0
    assert 0.0 <= res.fusion_score <= 1.0


def test_confidence_classifier_tiers():
    """Verify decision status and confidence tier assignment."""
    config = FusionConfig()
    classifier = ConfidenceClassifier(config)
    normalizer = EvidenceNormalizer()

    # Candidate with complete, excellent evidence
    profile_top = CandidateEvidenceProfile(
        candidate_id="VAR_TOP",
        mutations="W159H",
        parent_enzyme="IsPETase",
        protein_ai_feature=normalizer.normalize_protein_ai("VAR_TOP", raw_prediction=0.95),
        uncertainty_feature=normalizer.normalize_uncertainty_quality("VAR_TOP", raw_uncertainty=0.15),
        mechanism_feature=normalizer.normalize_mechanism_proximity("VAR_TOP", min_distance_angstrom=3.2),
        chemistry_feature=normalizer.normalize_chemistry_evidence("VAR_TOP", geometry_status="valid", scf_converged=True),
        quantum_feature=normalizer.normalize_quantum_evidence("VAR_TOP", vqe_casci_error=0.008),
        diversity_feature=normalizer.normalize_diversity("VAR_TOP", raw_diversity=0.85),
    )

    scorer = CompositeScorer(config)
    score_res = scorer.score_candidate(profile_top)
    classification = classifier.classify(profile_top, score_res)

    assert classification.decision_status == "PRIORITIZE"
    assert classification.confidence_label == "HIGH_CONFIDENCE"
    assert classification.uncertainty_flag == "LOW"


def test_deterministic_ranker_tie_breaking():
    """Verify deterministic multi-tier tie-breaking in CandidateRanker."""
    normalizer = EvidenceNormalizer()

    # Candidate A and B have identical fusion score, but Candidate A has higher coverage
    p_a = CandidateEvidenceProfile(
        candidate_id="VAR_A",
        mutations="S160G",
        parent_enzyme="IsPETase",
        protein_ai_feature=normalizer.normalize_protein_ai("VAR_A", raw_prediction=0.80),
        uncertainty_feature=normalizer.normalize_uncertainty_quality("VAR_A", raw_uncertainty=0.20),
        mechanism_feature=normalizer.normalize_mechanism_proximity("VAR_A", min_distance_angstrom=4.0),
        chemistry_feature=normalizer.normalize_chemistry_evidence("VAR_A", geometry_status="valid", scf_converged=True),
        quantum_feature=normalizer.normalize_quantum_evidence("VAR_A", vqe_casci_error=0.010),
        diversity_feature=normalizer.normalize_diversity("VAR_A", raw_diversity=0.80),
    )

    p_b = CandidateEvidenceProfile(
        candidate_id="VAR_B",
        mutations="S160T",
        parent_enzyme="IsPETase",
        protein_ai_feature=normalizer.normalize_protein_ai("VAR_B", raw_prediction=0.80),
        uncertainty_feature=normalizer.normalize_uncertainty_quality("VAR_B", raw_uncertainty=0.20),
        mechanism_feature=normalizer.normalize_mechanism_proximity("VAR_B", min_distance_angstrom=4.0),
        chemistry_feature=normalizer.normalize_chemistry_evidence("VAR_B", calculation_status="MISSING"),
        quantum_feature=normalizer.normalize_quantum_evidence("VAR_B", vqe_casci_error=None),
        diversity_feature=normalizer.normalize_diversity("VAR_B", raw_diversity=0.80),
    )

    ranker = CandidateRanker(FusionConfig())
    ranked = ranker.rank_candidates([p_b, p_a])  # Input in reverse order

    assert len(ranked) == 2
    assert ranked[0].candidate_id == "VAR_A"
    assert ranked[0].rank == 1
    assert ranked[1].candidate_id == "VAR_B"
    assert ranked[1].rank == 2


def test_rule_based_explanations():
    """Verify deterministic generation of candidate explanations and factor breakdowns."""
    normalizer = EvidenceNormalizer()
    p = CandidateEvidenceProfile(
        candidate_id="VAR_001",
        mutations="W159H",
        parent_enzyme="IsPETase",
        protein_ai_feature=normalizer.normalize_protein_ai("VAR_001", raw_prediction=0.92),
        uncertainty_feature=normalizer.normalize_uncertainty_quality("VAR_001", raw_uncertainty=0.10),
        mechanism_feature=normalizer.normalize_mechanism_proximity("VAR_001", min_distance_angstrom=3.0),
        chemistry_feature=normalizer.normalize_chemistry_evidence("VAR_001", geometry_status="valid", scf_converged=True),
        quantum_feature=normalizer.normalize_quantum_evidence("VAR_001", vqe_casci_error=0.009),
        diversity_feature=normalizer.normalize_diversity("VAR_001", raw_diversity=0.85),
        quantum_backend_type="SIMULATOR",
        integral_backend="CLASSICAL_FALLBACK",
        vqe_casci_error=0.009,
    )

    scorer = CompositeScorer()
    score_res = scorer.score_candidate(p)
    classifier = ConfidenceClassifier()
    cls = classifier.classify(p, score_res)

    engine = ExplanationEngine()
    exp = engine.generate_explanation(p, score_res, cls, rank=1)

    assert exp.candidate_id == "VAR_001"
    assert exp.rank == 1
    assert len(exp.positive_factors) >= 3
    assert any("protein sequence fitness" in factor for factor in exp.positive_factors)
    assert any("computational triage" in limit for limit in exp.limitations)
    assert any("SIMULATOR" in limit.upper() or "simulator" in limit.lower() for limit in exp.limitations)
