"""Integration tests for Phase 6 Evidence Fusion & Candidate Decision Pipeline."""

import json
from pathlib import Path
import pytest
import pandas as pd

from data.contracts import FILE_CONTRACTS, verify_contract
from fusion.config import FusionConfig
from fusion.evaluate import run_fusion_pipeline
from fusion.evidence import EvidenceAggregator
from fusion.outputs import FusionOutputWriter
from fusion.ranker import CandidateRanker


def test_phase6_end_to_end_pipeline(tmp_path: Path):
    """Verify complete end-to-end evidence aggregation, ranking, serialization, and contract conformance."""
    # 1. Create realistic mock upstream parquet tables
    df_ai = pd.DataFrame([
        {"variant_id": "VAR_001", "prediction": 0.92, "zero_shot_score": 0.88, "esm_log_likelihood_ratio": 2.1, "model_version": "v1", "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"},
        {"variant_id": "VAR_002", "prediction": 0.74, "zero_shot_score": 0.70, "esm_log_likelihood_ratio": 1.4, "model_version": "v1", "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"},
        {"variant_id": "VAR_003", "prediction": 0.35, "zero_shot_score": 0.40, "esm_log_likelihood_ratio": -0.5, "model_version": "v1", "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"},
    ])

    df_unc = pd.DataFrame([
        {"variant_id": "VAR_001", "prediction": 0.92, "ensemble_std": 0.08, "ood_score": 0.12, "conformal_lower": 0.84, "conformal_upper": 0.98, "uncertainty_score": 0.08},
        {"variant_id": "VAR_002", "prediction": 0.74, "ensemble_std": 0.25, "ood_score": 0.35, "conformal_lower": 0.55, "conformal_upper": 0.89, "uncertainty_score": 0.25},
        {"variant_id": "VAR_003", "prediction": 0.35, "ensemble_std": 0.45, "ood_score": 0.65, "conformal_lower": 0.10, "conformal_upper": 0.60, "uncertainty_score": 0.45},
    ])

    df_acq = pd.DataFrame([
        {"job_id": "JOB_001", "variant_id": "VAR_001", "mutations": "W159H", "parent_enzyme": "IsPETase", "predicted_performance": 0.92, "acquisition_score": 0.89, "diversity_score": 0.82, "selection_rank": 1, "selection_reason": "Top multi-objective score"},
        {"job_id": "JOB_002", "variant_id": "VAR_002", "mutations": "S160A", "parent_enzyme": "IsPETase", "predicted_performance": 0.74, "acquisition_score": 0.68, "diversity_score": 0.75, "selection_rank": 2, "selection_reason": "Catalytic proximity"},
        {"job_id": "JOB_003", "variant_id": "VAR_003", "mutations": "G200A", "parent_enzyme": "IsPETase", "predicted_performance": 0.35, "acquisition_score": 0.32, "diversity_score": 0.60, "selection_rank": 3, "selection_reason": "Diverse candidate"},
    ])

    df_chem = pd.DataFrame([
        {"variant_id": "VAR_001", "cluster_id": "CL_001", "geometry_source": "5XJH", "geometry_status": "valid", "method": "HF", "basis": "sto-3g", "scf_converged": True, "total_energy": -350.25, "delta_energy": -0.05, "calculation_status": "COMPLETED", "min_mutation_distance_to_active_site": 3.2},
        {"variant_id": "VAR_002", "cluster_id": "CL_002", "geometry_source": "5XJH", "geometry_status": "valid", "method": "HF", "basis": "sto-3g", "scf_converged": True, "total_energy": -349.80, "delta_energy": 0.02, "calculation_status": "COMPLETED", "min_mutation_distance_to_active_site": 4.1},
    ])

    df_qm = pd.DataFrame([
        {"variant_id": "VAR_001", "active_electrons": 4, "active_orbitals": 4, "initial_qubits": 8, "final_qubits": 8, "mapping_method": "jordan_wigner", "casci_energy": -3.8542, "vqe_energy": -3.8450, "vqe_absolute_error": 0.0092, "optimizer": "COBYLA", "iterations": 45, "calculation_status": "COMPLETED"},
    ])

    # Configure temporary test output paths
    out_results = tmp_path / "fusion_results.parquet"
    out_matrix = tmp_path / "evidence_matrix.parquet"
    out_manifest = tmp_path / "fusion_manifest.json"
    out_explanations = tmp_path / "candidate_explanations.json"

    cfg = FusionConfig(
        output_results_parquet=out_results,
        output_evidence_matrix_parquet=out_matrix,
        output_manifest_json=out_manifest,
        output_explanations_json=out_explanations,
    )

    # 2. Run Aggregation with direct DataFrames
    aggregator = EvidenceAggregator(cfg)
    profiles = aggregator.aggregate_evidence(
        protein_ai_df=df_ai,
        uncertainty_df=df_unc,
        acquisition_df=df_acq,
        chemistry_df=df_chem,
        quantum_df=df_qm,
    )

    assert len(profiles) == 3

    # 3. Rank
    ranker = CandidateRanker(cfg)
    ranked = ranker.rank_candidates(profiles)

    assert len(ranked) == 3
    assert ranked[0].candidate_id == "VAR_001"
    assert ranked[0].rank == 1
    assert ranked[0].decision_status == "PRIORITIZE"
    assert ranked[0].evidence_coverage_score == pytest.approx(6.0 / 6.0)
    assert ranked[0].synthetic_data_present is True
    assert ranked[0].quantum_backend_type == "SIMULATOR"
    assert ranked[0].integral_backend == "CLASSICAL_FALLBACK"

    # Candidate with missing chemistry & quantum (VAR_003)
    assert ranked[2].candidate_id == "VAR_003"
    assert ranked[2].missing_evidence_count >= 2
    assert ranked[2].decision_status == "LOW_PRIORITY"

    # 4. Save Outputs
    writer = FusionOutputWriter(cfg)
    saved = writer.save_all(ranked, profiles)

    assert out_results.exists()
    assert out_matrix.exists()
    assert out_manifest.exists()
    assert out_explanations.exists()

    # 5. Verify Parquet tables content
    res_df = pd.read_parquet(out_results)
    assert len(res_df) == 3
    assert "rank" in res_df.columns
    assert "fusion_score" in res_df.columns
    assert "decision_status" in res_df.columns

    matrix_df = pd.read_parquet(out_matrix)
    assert len(matrix_df) == 3 * 6  # 3 candidates x 6 channels = 18 rows
    assert "evidence_name" in matrix_df.columns
    assert "data_quality_flag" in matrix_df.columns

    # 6. Verify Manifest JSON
    with open(out_manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert manifest_data["candidate_count"] == 3
    assert manifest_data["provenance_and_backends"]["quantum_backend_type"] == "SIMULATOR"

    # 7. Verify Explanations JSON
    with open(out_explanations, "r", encoding="utf-8") as f:
        exp_data = json.load(f)
    assert "VAR_001" in exp_data["by_id"]
    assert exp_data["by_id"]["VAR_001"]["rank"] == 1
    assert len(exp_data["by_id"]["VAR_001"]["positive_factors"]) > 0
