"""Phase 6: Multimodal Evidence Fusion & Candidate Decision Engine."""

from fusion.confidence import ConfidenceClassifier, DecisionClassification
from fusion.config import DecisionThresholdsConfig, EvidenceWeightsConfig, FusionConfig
from fusion.evidence import CandidateEvidenceProfile, EvidenceAggregator
from fusion.explanations import CandidateExplanation, ExplanationEngine
from fusion.normalize import EvidenceNormalizer, NormalizedFeature
from fusion.outputs import FusionOutputWriter
from fusion.ranker import CandidateRanker, RankedCandidate
from fusion.scoring import CompositeScorer, FusionScoreResult

__all__ = [
    "FusionConfig",
    "EvidenceWeightsConfig",
    "DecisionThresholdsConfig",
    "EvidenceNormalizer",
    "NormalizedFeature",
    "CandidateEvidenceProfile",
    "EvidenceAggregator",
    "CompositeScorer",
    "FusionScoreResult",
    "ConfidenceClassifier",
    "DecisionClassification",
    "ExplanationEngine",
    "CandidateExplanation",
    "CandidateRanker",
    "RankedCandidate",
    "FusionOutputWriter",
]
