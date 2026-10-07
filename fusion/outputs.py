"""Serialization and export of Phase 6 fusion results, evidence matrix, manifest, and explanations."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from fusion.config import FusionConfig
from fusion.evidence import CandidateEvidenceProfile
from fusion.ranker import RankedCandidate


class FusionOutputWriter:
    """Serializes all Phase 6 candidate ranking outputs and evidence records."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()

    def build_fusion_results_df(self, ranked_candidates: List[RankedCandidate]) -> pd.DataFrame:
        """Builds the primary candidate triage ranking DataFrame."""
        rows = []
        for c in ranked_candidates:
            rows.append({
                "rank": c.rank,
                "candidate_id": c.candidate_id,
                "mutations": c.mutations,
                "parent_enzyme": c.parent_enzyme,
                "fusion_score": round(c.fusion_score, 4),
                "decision_status": c.decision_status,
                "confidence_label": c.confidence_label,
                "uncertainty_flag": c.uncertainty_flag,
                "evidence_coverage_score": round(c.evidence_coverage_score, 4),
                "available_evidence_count": c.available_evidence_count,
                "missing_evidence_count": c.missing_evidence_count,
                "protein_ai_score": round(c.protein_ai_score, 4),
                "uncertainty_quality_score": round(c.uncertainty_quality_score, 4),
                "mechanism_proximity_score": round(c.mechanism_proximity_score, 4),
                "chemistry_score": round(c.chemistry_score, 4),
                "quantum_score": round(c.quantum_score, 4),
                "diversity_score": round(c.diversity_score, 4),
                "protein_ai_available": c.protein_ai_available,
                "uncertainty_available": c.uncertainty_available,
                "mechanism_available": c.mechanism_available,
                "chemistry_available": c.chemistry_available,
                "quantum_available": c.quantum_available,
                "diversity_available": c.diversity_available,
                "quantum_backend_type": c.quantum_backend_type,
                "integral_backend": c.integral_backend,
                "vqe_casci_error": round(c.vqe_casci_error, 6) if c.vqe_casci_error is not None else None,
                "synthetic_data_present": c.synthetic_data_present,
                "summary": c.explanation.summary,
                "limitations": "; ".join(c.explanation.limitations),
            })
        return pd.DataFrame(rows)

    def build_evidence_matrix_df(self, profiles: List[CandidateEvidenceProfile]) -> pd.DataFrame:
        """Builds the detailed, granular evidence normalization provenance matrix."""
        rows = []
        for p in profiles:
            features = [
                p.protein_ai_feature,
                p.uncertainty_feature,
                p.mechanism_feature,
                p.chemistry_feature,
                p.quantum_feature,
                p.diversity_feature,
            ]
            for feat in features:
                rows.append({
                    "candidate_id": p.candidate_id,
                    "evidence_name": feat.evidence_name,
                    "raw_value": str(feat.raw_value) if feat.raw_value is not None else "None",
                    "normalized_value": round(feat.normalized_value, 4),
                    "normalization_method": feat.normalization_method,
                    "source_module": feat.source_module,
                    "source_artifact": feat.source_artifact,
                    "data_quality_flag": feat.data_quality_flag,
                    "available": feat.available,
                    "synthetic": feat.synthetic,
                })
        return pd.DataFrame(rows)

    def build_fusion_manifest(
        self,
        ranked_candidates: List[RankedCandidate],
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Constructs run metadata, triage statistics, and scientific provenance statements."""
        status_counts: Dict[str, int] = {}
        conf_counts: Dict[str, int] = {}
        for c in ranked_candidates:
            status_counts[c.decision_status] = status_counts.get(c.decision_status, 0) + 1
            conf_counts[c.confidence_label] = conf_counts.get(c.confidence_label, 0) + 1

        manifest = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": "Phase 6 - Evidence Fusion & Candidate Decision Engine",
            "candidate_count": len(ranked_candidates),
            "weights_configured": {
                "protein_ai": self.config.weights.protein_ai_weight,
                "uncertainty_quality": self.config.weights.uncertainty_quality_weight,
                "mechanism_proximity": self.config.weights.mechanism_proximity_weight,
                "chemistry_evidence": self.config.weights.chemistry_evidence_weight,
                "quantum_evidence": self.config.weights.quantum_evidence_weight,
                "diversity": self.config.weights.diversity_weight,
            },
            "policies": {
                "missing_evidence_policy": self.config.missing_evidence_policy,
                "synthetic_data_policy": self.config.synthetic_data_policy,
            },
            "triage_summary": {
                "decision_status_distribution": status_counts,
                "confidence_label_distribution": conf_counts,
            },
            "provenance_and_backends": {
                "quantum_backend_type": "SIMULATOR",
                "quantum_execution": "Classical statevector/Aer simulation of (4e, 4o) 8-qubit active-space Hamiltonian",
                "integral_backend": "CLASSICAL_FALLBACK (derived from model active-space integrals)",
                "experimental_validation": "NOT_AVAILABLE (Computational triage recommendation only)",
                "data_quality_notice": "Pipeline utilizes synthetic/test fixtures where local benchmark datasets are absent",
            },
            "scientific_guardrails": [
                "Ranking reflects computational triage priority, NOT experimental proof of enzyme degradation.",
                "Quantum simulation performed on classical simulator without claiming quantum hardware execution or advantage.",
                "No biological kinetic parameters or conversion yields have been fabricated.",
            ],
            "outputs": {
                "fusion_results_parquet": str(self.config.output_results_parquet),
                "evidence_matrix_parquet": str(self.config.output_evidence_matrix_parquet),
                "fusion_manifest_json": str(self.config.output_manifest_json),
                "candidate_explanations_json": str(self.config.output_explanations_json),
            },
        }
        if extra_metadata:
            manifest.update(extra_metadata)
        return manifest

    def build_explanations_json(self, ranked_candidates: List[RankedCandidate]) -> Dict[str, Any]:
        """Constructs dictionary of candidate explanations indexed by candidate_id and list."""
        return {
            "candidates": [c.explanation.to_dict() for c in ranked_candidates],
            "by_id": {c.candidate_id: c.explanation.to_dict() for c in ranked_candidates},
        }

    def save_all(
        self,
        ranked_candidates: List[RankedCandidate],
        profiles: List[CandidateEvidenceProfile],
    ) -> Dict[str, Path]:
        """Writes all Phase 6 outputs to disk."""
        out_dir = self.config.output_results_parquet.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Primary results table
        results_df = self.build_fusion_results_df(ranked_candidates)
        results_df.to_parquet(self.config.output_results_parquet, index=False)

        # 2. Evidence matrix
        matrix_df = self.build_evidence_matrix_df(profiles)
        matrix_df.to_parquet(self.config.output_evidence_matrix_parquet, index=False)

        # 3. Fusion manifest
        manifest = self.build_fusion_manifest(ranked_candidates)
        with open(self.config.output_manifest_json, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 4. Candidate explanations
        explanations = self.build_explanations_json(ranked_candidates)
        with open(self.config.output_explanations_json, "w", encoding="utf-8") as f:
            json.dump(explanations, f, indent=2)

        return {
            "fusion_results": self.config.output_results_parquet,
            "evidence_matrix": self.config.output_evidence_matrix_parquet,
            "fusion_manifest": self.config.output_manifest_json,
            "candidate_explanations": self.config.output_explanations_json,
        }
