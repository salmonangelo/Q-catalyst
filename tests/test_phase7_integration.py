"""Integration test for Phase 7 End-to-End Pipeline Execution."""

import json
from pathlib import Path
import pytest
import pandas as pd

from pipeline.config import PipelineConfig, QuantumPolicyConfig
from pipeline.evaluate import run_pipeline_cli
from pipeline.runner import PipelineRunner


def test_phase7_end_to_end_orchestration(tmp_path: Path):
    """Verify complete end-to-end execution of all 7 pipeline stages on test fixtures."""
    # 1. Setup mock workspace fixtures
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    var_path = fixtures_dir / "variants.parquet"
    pred_path = fixtures_dir / "predictions.parquet"
    unc_path = fixtures_dir / "uncertainty.parquet"
    g0_path = fixtures_dir / "gate0_report.json"
    acq_path = fixtures_dir / "selected_candidates.parquet"
    jobs_path = fixtures_dir / "chem_jobs.json"
    chem_path = fixtures_dir / "chem_results.parquet"
    cluster_manifest_path = fixtures_dir / "cluster_manifest.json"
    qm_path = fixtures_dir / "quantum_results.parquet"
    qm_manifest_path = fixtures_dir / "quantum_manifest.json"
    fusion_results_path = fixtures_dir / "fusion_results.parquet"
    evidence_matrix_path = fixtures_dir / "evidence_matrix.parquet"
    fusion_manifest_path = fixtures_dir / "fusion_manifest.json"
    candidate_exp_path = fixtures_dir / "candidate_explanations.json"

    # Write minimal mock variants dataframe with 3 candidates
    df_var = pd.DataFrame([
        {"variant_id": "VAR_001", "parent_enzyme": "IsPETase", "sequence": "MNFPRASRLMQAAVLGGLMAVSAAATAQTNP", "mutations": "W159H", "activity_value": 1.25, "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"},
        {"variant_id": "VAR_002", "parent_enzyme": "IsPETase", "sequence": "MNFPRASRLMQAAVLGGLMAVSAAATAQTNP", "mutations": "S160A", "activity_value": 0.85, "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"},
        {"variant_id": "VAR_003", "parent_enzyme": "IsPETase", "sequence": "MNFPRASRLMQAAVLGGLMAVSAAATAQTNP", "mutations": "G200A", "activity_value": 0.40, "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"},
    ])
    df_var.to_parquet(var_path, index=False)

    df_preds = pd.DataFrame([
        {"variant_id": "VAR_001", "prediction": 0.92, "zero_shot_score": 0.88, "esm_log_likelihood_ratio": 2.1, "model_version": "v1"},
        {"variant_id": "VAR_002", "prediction": 0.74, "zero_shot_score": 0.70, "esm_log_likelihood_ratio": 1.4, "model_version": "v1"},
        {"variant_id": "VAR_003", "prediction": 0.35, "zero_shot_score": 0.40, "esm_log_likelihood_ratio": -0.5, "model_version": "v1"},
    ])
    df_preds.to_parquet(pred_path, index=False)

    df_unc = pd.DataFrame([
        {"variant_id": "VAR_001", "prediction": 0.92, "ensemble_std": 0.08, "ood_score": 0.12, "conformal_lower": 0.84, "conformal_upper": 0.98, "uncertainty_score": 0.08},
        {"variant_id": "VAR_002", "prediction": 0.74, "ensemble_std": 0.25, "ood_score": 0.35, "conformal_lower": 0.55, "conformal_upper": 0.89, "uncertainty_score": 0.25},
        {"variant_id": "VAR_003", "prediction": 0.35, "ensemble_std": 0.45, "ood_score": 0.65, "conformal_lower": 0.10, "conformal_upper": 0.60, "uncertainty_score": 0.45},
    ])
    df_unc.to_parquet(unc_path, index=False)

    with open(g0_path, "w", encoding="utf-8") as f:
        json.dump({"useful_signal": True, "spearman_correlation": 0.65, "limitations": []}, f)

    df_acq = pd.DataFrame([
        {"job_id": "JOB_001", "variant_id": "VAR_001", "mutations": "W159H", "parent_enzyme": "IsPETase", "predicted_performance": 0.92, "acquisition_score": 0.89, "diversity_score": 0.82, "selection_rank": 1, "selection_reason": "Top multi-objective score"},
        {"job_id": "JOB_002", "variant_id": "VAR_002", "mutations": "S160A", "parent_enzyme": "IsPETase", "predicted_performance": 0.74, "acquisition_score": 0.68, "diversity_score": 0.75, "selection_rank": 2, "selection_reason": "Catalytic proximity"},
    ])
    df_acq.to_parquet(acq_path, index=False)

    with open(jobs_path, "w", encoding="utf-8") as f:
        json.dump([{"job_id": "JOB_001", "variant_id": "VAR_001", "mutations": "W159H", "active_site_residues": [160, 206, 237], "qm_method_requested": "VQE", "selection_rank": 1}], f)

    df_chem = pd.DataFrame([
        {"variant_id": "VAR_001", "cluster_id": "CL_001", "geometry_source": "5XJH", "geometry_status": "valid", "method": "HF", "basis": "sto-3g", "scf_converged": True, "total_energy": -350.25, "delta_energy": -0.05, "calculation_status": "COMPLETED", "min_mutation_distance_to_active_site": 3.2},
        {"variant_id": "VAR_002", "cluster_id": "CL_002", "geometry_source": "5XJH", "geometry_status": "valid", "method": "HF", "basis": "sto-3g", "scf_converged": True, "total_energy": -349.80, "delta_energy": 0.02, "calculation_status": "COMPLETED", "min_mutation_distance_to_active_site": 4.1},
    ])
    df_chem.to_parquet(chem_path, index=False)

    with open(cluster_manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "1.0", "cluster_count": 2, "clusters": []}, f)

    df_qm = pd.DataFrame([
        {"variant_id": "VAR_001", "active_electrons": 4, "active_orbitals": 4, "initial_qubits": 8, "final_qubits": 8, "mapping_method": "jordan_wigner", "casci_energy": -3.8542, "vqe_energy": -3.8450, "vqe_absolute_error": 0.0092, "optimizer": "COBYLA", "iterations": 45, "calculation_status": "COMPLETED"},
    ])
    df_qm.to_parquet(qm_path, index=False)

    with open(qm_manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": "1.0", "variant_id": "VAR_001", "active_space": {}, "qubit_hamiltonian": {}, "casci_reference": {}, "vqe_results": {}}, f)

    # 2. Configure Pipeline to run in temporary output directory
    runs_dir = tmp_path / "runs"
    cfg = PipelineConfig(
        output_root=runs_dir,
        reuse_cached_outputs=True,
        variants_parquet=var_path,
        protein_ai_parquet=pred_path,
        uncertainty_parquet=unc_path,
        gate0_report_json=g0_path,
        acquisition_parquet=acq_path,
        chem_jobs_json=jobs_path,
        chemistry_parquet=chem_path,
        cluster_manifest_json=cluster_manifest_path,
        quantum_parquet=qm_path,
        quantum_manifest_json=qm_manifest_path,
        fusion_results_parquet=fusion_results_path,
        evidence_matrix_parquet=evidence_matrix_path,
        fusion_manifest_json=fusion_manifest_path,
        candidate_explanations_json=candidate_exp_path,
    )

    # 3. Run Pipeline Orchestrator
    runner = PipelineRunner(cfg)
    context = runner.run(cfg)

    # 4. Verify context and stage execution
    assert context.candidate_count == 3
    assert len(context.stage_status) == 7
    for stage in cfg.enabled_stages:
        assert context.stage_status[stage] in ("SUCCESS", "SUCCESS_CACHED")

    assert context.synthetic_data_present is True
    assert context.quantum_backend_type == "SIMULATOR"
    assert context.integral_backend == "CLASSICAL_FALLBACK"

    # 5. Verify Run Directory Artifacts
    run_dir = context.run_dir
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "pipeline_report.json").exists()
    assert (run_dir / "pipeline_report.md").exists()
    assert (run_dir / "logs" / "pipeline.log").exists()

    # 6. Check Manifest Content
    with open(run_dir / "manifest.json", "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert manifest_data["candidates"]["count"] == 3
    assert manifest_data["scientific_claims_policy"]["experimental_validation"] is False
    assert manifest_data["scientific_claims_policy"]["quantum_advantage"] is False
    assert manifest_data["provenance_and_backends"]["quantum_backend_type"] == "SIMULATOR"

    # 7. Check Final Triage Ranking
    assert len(context.final_ranking) >= 1
    assert context.final_ranking[0]["candidate_id"] == "VAR_001"
    assert context.final_ranking[0]["decision_status"] == "PRIORITIZE"
