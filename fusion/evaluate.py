"""Phase 6 Evaluation Pipeline and CLI Entry Point.

Executes multimodal evidence aggregation, composite scoring, deterministic ranking,
rule-based explainability, and artifact serialization.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from fusion.config import FusionConfig
from fusion.evidence import EvidenceAggregator
from fusion.outputs import FusionOutputWriter
from fusion.ranker import CandidateRanker


def load_config_from_yaml(config_path: Path = Path("configs/config.yaml")) -> FusionConfig:
    """Loads fusion configuration from project YAML if available, else returns defaults."""
    if not config_path.exists():
        return FusionConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg_dict = yaml.safe_load(f) or {}

        fusion_dict = cfg_dict.get("fusion", {})
        if not fusion_dict:
            return FusionConfig()

        # Parse weights and thresholds if nested
        weights = fusion_dict.get("weights", {})
        thresholds = fusion_dict.get("thresholds", {})
        
        return FusionConfig(
            weights=weights if weights else None,
            thresholds=thresholds if thresholds else None,
            missing_evidence_policy=fusion_dict.get("missing_evidence_policy", "renormalize_available"),
            synthetic_data_policy=fusion_dict.get("synthetic_data_policy", "preserve_provenance"),
            protein_ai_path=Path(fusion_dict.get("protein_ai_path", "protein_ai/predictions.parquet")),
            uncertainty_path=Path(fusion_dict.get("uncertainty_path", "uncertainty/uncertainty.parquet")),
            acquisition_path=Path(fusion_dict.get("acquisition_path", "acquisition/selected_candidates.parquet")),
            chemistry_path=Path(fusion_dict.get("chemistry_path", "chemistry/chem_results.parquet")),
            quantum_path=Path(fusion_dict.get("quantum_path", "quantum/quantum_results.parquet")),
            output_results_parquet=Path(fusion_dict.get("output_results_parquet", "fusion/fusion_results.parquet")),
            output_evidence_matrix_parquet=Path(fusion_dict.get("output_evidence_matrix_parquet", "fusion/evidence_matrix.parquet")),
            output_manifest_json=Path(fusion_dict.get("output_manifest_json", "fusion/fusion_manifest.json")),
            output_explanations_json=Path(fusion_dict.get("output_explanations_json", "fusion/candidate_explanations.json")),
        )
    except Exception as e:
        print(f"Warning: Could not parse YAML config ({e}). Using default FusionConfig.")
        return FusionConfig()


def run_fusion_pipeline(
    config: Optional[FusionConfig] = None,
    verbose: bool = True,
):
    """Executes the end-to-end evidence fusion and candidate decision pipeline."""
    cfg = config or load_config_from_yaml()

    # 1. Aggregate evidence from upstream artifacts
    aggregator = EvidenceAggregator(cfg)
    profiles = aggregator.aggregate_evidence()

    if not profiles:
        if verbose:
            print("No candidate evidence records found in upstream artifacts.")
        return [], []

    # 2. Rank candidates deterministically
    ranker = CandidateRanker(cfg)
    ranked_candidates = ranker.rank_candidates(profiles)

    # 3. Write output artifacts
    writer = FusionOutputWriter(cfg)
    saved_paths = writer.save_all(ranked_candidates, profiles)

    # 4. Print structured summary
    if verbose:
        print("\n============================================================")
        print("Q-CATALYST Evidence Fusion & Candidate Decision Engine")
        print("============================================================")
        print(f"Candidates processed: {len(ranked_candidates)}")
        print(f"Evidence channels configured: 6")
        print(f"Missing-evidence policy: {cfg.missing_evidence_policy}")
        print(f"Weights: AI={cfg.weights.protein_ai_weight:.2f}, "
              f"Unc={cfg.weights.uncertainty_quality_weight:.2f}, "
              f"Mech={cfg.weights.mechanism_proximity_weight:.2f}, "
              f"Chem={cfg.weights.chemistry_evidence_weight:.2f}, "
              f"QM={cfg.weights.quantum_evidence_weight:.2f}, "
              f"Div={cfg.weights.diversity_weight:.2f}")
        print("------------------------------------------------------------")
        print("Top Prioritized Candidates:")
        for c in ranked_candidates[:10]:
            qm_info = f"VQE-CASCI err={c.vqe_casci_error:.4f} Ha" if c.vqe_casci_error is not None else "QM=N/A"
            print(f"  {c.rank:2d}. {c.candidate_id:<12} score={c.fusion_score:.4f}  "
                  f"status={c.decision_status:<24} coverage={c.available_evidence_count}/6  "
                  f"conf={c.confidence_label:<19} [{qm_info}]")

        print("------------------------------------------------------------")
        synthetic_flag = "YES (synthetic test fixtures present)" if any(c.synthetic_data_present for c in ranked_candidates) else "NO"
        print(f"Quantum backend:       SIMULATOR (Statevector / Aer)")
        print(f"Integral backend:      CLASSICAL_FALLBACK")
        print(f"Experimental validation: NOT AVAILABLE (Computational triage only)")
        print(f"Synthetic benchmark:   {synthetic_flag}")
        print("============================================================\n")

    return ranked_candidates, profiles


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Q-Catalyst Phase 6 Evidence Fusion Engine")
    parser.add_argument("--config", type=str, default="configs/config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    cfg = load_config_from_yaml(Path(args.config))
    run_fusion_pipeline(cfg, verbose=True)


if __name__ == "__main__":
    main()
