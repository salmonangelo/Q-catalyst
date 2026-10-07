"""Decision-status triage classification and evidence confidence assessment."""

from dataclasses import dataclass
from typing import Optional

from fusion.config import DecisionThresholdsConfig, FusionConfig
from fusion.evidence import CandidateEvidenceProfile
from fusion.scoring import FusionScoreResult


@dataclass
class DecisionClassification:
    """Triage categorization and confidence labeling for a candidate."""
    candidate_id: str
    decision_status: str  # "PRIORITIZE", "PROMISING_BUT_UNCERTAIN", "INSUFFICIENT_EVIDENCE", "LOW_PRIORITY"
    confidence_label: str  # "HIGH_CONFIDENCE", "MODERATE_CONFIDENCE", "LOW_CONFIDENCE"
    uncertainty_flag: str  # "LOW", "MEDIUM", "HIGH", "UNKNOWN"


class ConfidenceClassifier:
    """Classifies candidates into standardized decision tiers and confidence levels."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()

    def classify(
        self,
        profile: CandidateEvidenceProfile,
        score_result: FusionScoreResult,
    ) -> DecisionClassification:
        """Assigns decision status, confidence tier, and uncertainty flag based on explicit thresholds."""
        thresh = self.config.thresholds
        score = score_result.fusion_score
        coverage = score_result.evidence_coverage_score
        unc_quality = profile.uncertainty_quality_score
        unc_available = profile.uncertainty_feature.available

        # 1. Uncertainty Flag
        if not unc_available:
            unc_flag = "UNKNOWN"
        elif unc_quality >= (1.0 - thresh.uncertainty_low_threshold):
            unc_flag = "LOW"
        elif unc_quality <= (1.0 - thresh.uncertainty_high_threshold):
            unc_flag = "HIGH"
        else:
            unc_flag = "MEDIUM"

        # 2. Decision Status
        if coverage < thresh.insufficient_evidence_max_coverage:
            status = "INSUFFICIENT_EVIDENCE"
        elif score >= thresh.prioritize_min_score and coverage >= thresh.prioritize_min_coverage and unc_flag != "HIGH":
            status = "PRIORITIZE"
        elif score >= thresh.promising_min_score:
            status = "PROMISING_BUT_UNCERTAIN"
        else:
            status = "LOW_PRIORITY"

        # 3. Confidence Label (derived strictly from evidence coverage and uncertainty quality)
        if coverage >= 0.80 and unc_flag == "LOW":
            conf_label = "HIGH_CONFIDENCE"
        elif coverage >= 0.50 and unc_flag in ("LOW", "MEDIUM"):
            conf_label = "MODERATE_CONFIDENCE"
        else:
            conf_label = "LOW_CONFIDENCE"

        return DecisionClassification(
            candidate_id=profile.candidate_id,
            decision_status=status,
            confidence_label=conf_label,
            uncertainty_flag=unc_flag,
        )
