"""End-to-end integration tests for Phase 3 Smart Acquisition Gate."""

import json
from pathlib import Path
import pandas as pd
import pytest

from acquisition.config import AcquisitionConfig
from acquisition.evaluate import run_acquisition_pipeline
from data.contracts import verify_contract
from protein_ai.config import ProteinAIConfig
from protein_ai.inference import run_protein_ai_pipeline
from protein_ai.utils import create_synthetic_variant_dataset
from uncertainty.evaluate import run_uncertainty_evaluation


def test_phase3_full_pipeline_integration(tmp_path):
    # 1. Create synthetic fixture dataset
    df_synthetic = create_synthetic_variant_dataset(n_records=24, random_seed=42)
    variants_path = tmp_path / "data" / "curated" / "variants.parquet"
    variants_path.parent.mkdir(parents=True, exist_ok=True)
    df_synthetic.to_parquet(variants_path, engine="pyarrow", index=False)

    preds_path = tmp_path / "protein_ai" / "predictions.parquet"
    unc_path = tmp_path / "uncertainty" / "uncertainty.parquet"
    gate0_json = tmp_path / "uncertainty" / "gate0_report.json"
    gate0_md = tmp_path / "uncertainty" / "GATE0_REPORT.md"

    jobs_json = tmp_path / "acquisition" / "chem_jobs.json"
    cand_parquet = tmp_path / "acquisition" / "selected_candidates.parquet"

    # Configs
    p_cfg = ProteinAIConfig()
    p_cfg.esm.cache_dir = tmp_path / "cache"
    p_cfg.predictor.artifacts_dir = tmp_path / "artifacts"
    p_cfg.uncertainty.uncertainty_output_path = unc_path
    p_cfg.uncertainty.gate0_report_json = gate0_json
    p_cfg.uncertainty.gate0_report_md = gate0_md

    a_cfg = AcquisitionConfig(
        chemistry_budget=6,
        performance_quantile=0.50,
        output_jobs_json=jobs_json,
        output_candidates_parquet=cand_parquet,
    )

    # 2. Run Protein AI
    run_protein_ai_pipeline(
        variants_parquet=variants_path,
        output_predictions_path=preds_path,
        split_strategy="random",
        protein_ai_config=p_cfg,
    )

    # 3. Run Uncertainty
    run_uncertainty_evaluation(
        variants_parquet=variants_path,
        predictions_parquet=preds_path,
        output_uncertainty_path=unc_path,
        gate0_json_path=gate0_json,
        gate0_md_path=gate0_md,
        split_strategy="random",
        protein_ai_config=p_cfg,
    )

    # 4. Run Smart Acquisition
    selected, meta = run_acquisition_pipeline(
        predictions_parquet=preds_path,
        uncertainty_parquet=unc_path,
        variants_parquet=variants_path,
        gate0_json_path=gate0_json,
        output_jobs_json=jobs_json,
        output_candidates_parquet=cand_parquet,
        acquisition_config=a_cfg,
        is_synthetic_run=True,
    )

    # Verify outputs exist
    assert jobs_json.exists()
    assert cand_parquet.exists()
    assert len(selected) == 6
    assert meta["selected_count"] == 6

    # Verify contracts
    valid_jobs, job_issues = verify_contract("acquisition", base_dir=tmp_path)
    assert valid_jobs is True, f"chem_jobs.json contract violated: {job_issues}"

    valid_cands, cand_issues = verify_contract("acquisition_candidates", base_dir=tmp_path)
    assert valid_cands is True, f"selected_candidates.parquet contract violated: {cand_issues}"

    # Verify JSON content
    with open(jobs_json, "r", encoding="utf-8") as f:
        job_data = json.load(f)
    assert "metadata" in job_data
    assert "candidates" in job_data
    assert len(job_data["candidates"]) == 6
    assert job_data["candidates"][0]["selection_rank"] == 1


def test_acquisition_budget_shortfall(tmp_path):
    # Small synthetic pool with only 4 records, but budget is 10
    df_small = create_synthetic_variant_dataset(n_records=4, random_seed=42)
    variants_path = tmp_path / "variants.parquet"
    df_small.to_parquet(variants_path, engine="pyarrow", index=False)

    preds_path = tmp_path / "predictions.parquet"
    unc_path = tmp_path / "uncertainty.parquet"
    gate0_json = tmp_path / "gate0.json"
    jobs_json = tmp_path / "chem_jobs.json"
    cand_parquet = tmp_path / "selected_candidates.parquet"

    p_cfg = ProteinAIConfig()
    p_cfg.esm.cache_dir = tmp_path / "cache"
    p_cfg.predictor.artifacts_dir = tmp_path / "artifacts"
    p_cfg.uncertainty.uncertainty_output_path = unc_path
    p_cfg.uncertainty.gate0_report_json = gate0_json

    a_cfg = AcquisitionConfig(
        chemistry_budget=10,
        performance_quantile=None,  # Do not filter out
        output_jobs_json=jobs_json,
        output_candidates_parquet=cand_parquet,
    )

    run_protein_ai_pipeline(variants_parquet=variants_path, output_predictions_path=preds_path, protein_ai_config=p_cfg)
    run_uncertainty_evaluation(variants_parquet=variants_path, predictions_parquet=preds_path, output_uncertainty_path=unc_path, gate0_json_path=gate0_json, protein_ai_config=p_cfg)

    selected, meta = run_acquisition_pipeline(
        predictions_parquet=preds_path,
        uncertainty_parquet=unc_path,
        variants_parquet=variants_path,
        gate0_json_path=gate0_json,
        output_jobs_json=jobs_json,
        output_candidates_parquet=cand_parquet,
        acquisition_config=a_cfg,
        is_synthetic_run=True,
    )

    assert len(selected) == 4
    assert meta["requested_budget"] == 10
    assert meta["selected_count"] == 4
    assert meta["selection_shortfall"] == 6


def test_missing_predictions_error():
    with pytest.raises(FileNotFoundError, match="Predictions file not found"):
        run_acquisition_pipeline(
            predictions_parquet="non_existent/predictions.parquet",
            uncertainty_parquet="non_existent/uncertainty.parquet",
        )
