"""End-to-end integration tests for Phase 2: Protein-AI + Uncertainty + Gate 0."""

import json
from pathlib import Path
import pandas as pd
import pytest

from data.contracts import verify_contract
from protein_ai.config import ProteinAIConfig
from protein_ai.inference import run_protein_ai_pipeline
from protein_ai.utils import create_synthetic_variant_dataset
from uncertainty.evaluate import run_uncertainty_evaluation


def test_phase2_end_to_end_integration(tmp_path):
    # 1. Create synthetic fixture dataset
    df_synthetic = create_synthetic_variant_dataset(n_records=20, random_seed=42)
    assert (df_synthetic["data_source"] == "synthetic_test_fixture").all()

    variants_path = tmp_path / "data" / "curated" / "variants.parquet"
    variants_path.parent.mkdir(parents=True, exist_ok=True)
    df_synthetic.to_parquet(variants_path, engine="pyarrow", index=False)

    preds_path = tmp_path / "protein_ai" / "predictions.parquet"
    unc_path = tmp_path / "uncertainty" / "uncertainty.parquet"
    gate0_json = tmp_path / "uncertainty" / "gate0_report.json"
    gate0_md = tmp_path / "uncertainty" / "GATE0_REPORT.md"

    p_cfg = ProteinAIConfig()
    p_cfg.esm.cache_dir = tmp_path / "cache"
    p_cfg.predictor.artifacts_dir = tmp_path / "artifacts"
    p_cfg.uncertainty.uncertainty_output_path = unc_path
    p_cfg.uncertainty.gate0_report_json = gate0_json
    p_cfg.uncertainty.gate0_report_md = gate0_md

    # 2. Run Protein AI Inference
    pred_df, metrics = run_protein_ai_pipeline(
        variants_parquet=variants_path,
        output_predictions_path=preds_path,
        split_strategy="random",
        protein_ai_config=p_cfg,
    )

    assert preds_path.exists()
    assert len(pred_df) == 20
    assert "prediction" in pred_df.columns
    assert "esm_log_likelihood_ratio" in pred_df.columns

    # 3. Run Uncertainty & Gate 0 Evaluation
    unc_df, gate0_report = run_uncertainty_evaluation(
        variants_parquet=variants_path,
        predictions_parquet=preds_path,
        output_uncertainty_path=unc_path,
        gate0_json_path=gate0_json,
        gate0_md_path=gate0_md,
        split_strategy="random",
        protein_ai_config=p_cfg,
    )

    assert unc_path.exists()
    assert gate0_json.exists()
    assert gate0_md.exists()
    assert len(unc_df) == 20
    assert "uncertainty_score" in unc_df.columns
    assert "conformal_lower" in unc_df.columns
    assert "conformal_upper" in unc_df.columns

    # 4. Verify file contracts
    valid_pred, pred_issues = verify_contract("protein_ai", base_dir=tmp_path)
    assert valid_pred is True, f"Protein AI contract violated: {pred_issues}"

    valid_unc, unc_issues = verify_contract("uncertainty", base_dir=tmp_path)
    assert valid_unc is True, f"Uncertainty contract violated: {unc_issues}"

    # 5. Check Gate-0 report metadata
    with open(gate0_json, "r", encoding="utf-8") as f:
        g0_data = json.load(f)
    assert g0_data["error_metric"] == "MAE"
    assert "limitations" in g0_data
    assert any("TEST RUN ONLY" in lim for lim in g0_data["limitations"])


def test_missing_dataset_clean_error():
    with pytest.raises(FileNotFoundError, match="Curated variants dataset not found"):
        run_protein_ai_pipeline(
            variants_parquet="non_existent_data/variants.parquet"
        )
