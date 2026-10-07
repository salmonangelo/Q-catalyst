"""Orchestrator for uncertainty estimation, conformal calibration, and Gate-0 evaluation."""

import argparse
from pathlib import Path
import sys
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

# Ensure project root in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from configs.config_schema import QCatalystConfig, load_config
from data.split import DatasetSplitter, SplitManifest
from protein_ai.config import ProteinAIConfig
from protein_ai.embeddings import EmbeddingExtractor
from protein_ai.features import FeaturePipeline
from protein_ai.inference import run_protein_ai_pipeline
from protein_ai.mutation_scoring import MutationScorer
from uncertainty.conformal import ConformalCalibrator
from uncertainty.ensemble import EnsembleEstimator
from uncertainty.gate0 import Gate0Report, evaluate_gate0
from uncertainty.ood import OODDetector
from uncertainty.score import CompositeUncertaintyScorer

UNCERTAINTY_COLUMNS = [
    "variant_id",
    "prediction",
    "ensemble_mean",
    "ensemble_std",
    "ood_score",
    "conformal_lower",
    "conformal_upper",
    "uncertainty_score",
    "uncertainty_method",
    "model_version",
    "split_strategy",
]


def run_uncertainty_evaluation(
    variants_parquet: Optional[Path | str] = None,
    predictions_parquet: Optional[Path | str] = None,
    output_uncertainty_path: Optional[Path | str] = None,
    gate0_json_path: Optional[Path | str] = None,
    gate0_md_path: Optional[Path | str] = None,
    split_strategy: str = "mutation_complexity",
    protein_ai_config: Optional[ProteinAIConfig] = None,
    global_config: Optional[QCatalystConfig] = None,
) -> Tuple[pd.DataFrame, Gate0Report]:
    """Execute complete uncertainty estimation, conformal calibration, and Gate 0 verification.

    Args:
        variants_parquet: Path to curated variants parquet.
        predictions_parquet: Path to existing predictions parquet (or generated if missing).
        output_uncertainty_path: Destination for uncertainty.parquet.
        gate0_json_path: Destination for gate0_report.json.
        gate0_md_path: Destination for GATE0_REPORT.md.
        split_strategy: Split partitioning strategy.
        protein_ai_config: ProteinAIConfig instance.
        global_config: QCatalystConfig instance.

    Returns:
        Tuple of (uncertainty_dataframe, Gate0Report).
    """
    g_cfg = global_config or load_config()
    p_cfg = protein_ai_config or ProteinAIConfig()

    data_file = Path(variants_parquet or g_cfg.paths.curated_variants_file)
    pred_file = Path(predictions_parquet or g_cfg.downstream_contracts.protein_ai)
    out_unc = Path(output_uncertainty_path or p_cfg.uncertainty.uncertainty_output_path)
    out_g0_json = Path(gate0_json_path or p_cfg.uncertainty.gate0_report_json)
    out_g0_md = Path(gate0_md_path or p_cfg.uncertainty.gate0_report_md)

    if not data_file.exists():
        raise FileNotFoundError(f"Curated variants dataset not found at '{data_file}'.")

    # If predictions parquet does not exist, run protein AI inference first
    if not pred_file.exists():
        print(f"Predictions file not found at '{pred_file}'. Running Protein-AI inference first...")
        run_protein_ai_pipeline(
            variants_parquet=data_file,
            output_predictions_path=pred_file,
            split_strategy=split_strategy,
            protein_ai_config=p_cfg,
            global_config=g_cfg,
        )

    df_variants = pd.read_parquet(data_file)
    df_preds = pd.read_parquet(pred_file)

    # Merge on variant_id
    merged = pd.merge(df_variants, df_preds[["variant_id", "prediction", "split", "model_version"]], on="variant_id", how="inner")
    if merged.empty:
        raise ValueError("Merged variants and predictions DataFrame is empty.")

    is_synthetic = any(merged.get("data_quality_flag", "").str.contains("SYNTHETIC", na=False))

    # 1. Feature extraction
    feature_pipeline = FeaturePipeline(
        embedding_extractor=EmbeddingExtractor(config=p_cfg.esm),
        mutation_scorer=MutationScorer(config=p_cfg.esm),
        normalize_features=p_cfg.predictor.normalize_features,
    )

    train_mask = merged["split"] == "train"
    val_mask = merged["split"] == "val"
    test_mask = merged["split"] == "test"

    train_df = merged[train_mask]
    if len(train_df) == 0:
        # If no split assigned, use 70% as train
        train_mask = np.arange(len(merged)) < int(0.7 * len(merged))
        train_df = merged[train_mask]

    X_train, _ = feature_pipeline.fit_transform(train_df)
    X_all, _ = feature_pipeline.transform(merged)

    target_col = p_cfg.predictor.target_column
    if target_col not in merged.columns or merged[target_col].isna().all():
        target_col = "activity_value"

    y_train = train_df[target_col].values.astype(float)

    # 2. Ensemble Disagreement
    print(f"Training ensemble of {p_cfg.uncertainty.ensemble_size} models...")
    ensemble = EnsembleEstimator(predictor_config=p_cfg.predictor, uncertainty_config=p_cfg.uncertainty)
    ensemble.fit(X_train, y_train)
    ens_mean, ens_std = ensemble.predict_with_disagreement(X_all)

    # 3. OOD Distance Estimation
    print("Computing OOD geometric distances from training manifold...")
    ood_detector = OODDetector(config=p_cfg.uncertainty)
    ood_detector.fit(X_train)
    ood_scores = ood_detector.compute_ood_scores(X_all)

    # 4. Conformal Calibration on validation fold
    conformal = ConformalCalibrator(config=p_cfg.uncertainty)
    if val_mask.any() and pd.notna(merged.loc[val_mask, target_col]).any():
        y_val_t = merged.loc[val_mask, target_col].values.astype(float)
        y_val_p = merged.loc[val_mask, "prediction"].values.astype(float)
        try:
            conformal.calibrate(y_val_t, y_val_p)
            print(f"Calibrated Conformal Predictor: q = {conformal.quantile_q:.4f} (coverage: {1.0 - p_cfg.uncertainty.conformal_alpha:.0%})")
        except Exception as e:
            print(f"Warning: Conformal calibration on val set failed ({e}). Calibrating on train residuals.")
            conformal.calibrate(y_train, ens_mean[train_mask])
    else:
        # Calibrate on training residuals as fallback
        conformal.calibrate(y_train, ens_mean[train_mask])

    conf_intervals = conformal.predict_intervals(merged["prediction"].values)

    # 5. Composite Uncertainty Score
    scorer = CompositeUncertaintyScorer(config=p_cfg.uncertainty)
    composite_u, weights_used = scorer.compute_composite_score(
        ensemble_std=ens_std,
        ood_scores=ood_scores,
        conformal_width=conf_intervals.interval_width,
    )

    # Construct uncertainty DataFrame
    unc_df = pd.DataFrame({
        "variant_id": merged["variant_id"].astype("string"),
        "prediction": merged["prediction"].astype("float64"),
        "ensemble_mean": ens_mean.astype("float64"),
        "ensemble_std": ens_std.astype("float64"),
        "ood_score": ood_scores.astype("float64"),
        "conformal_lower": conf_intervals.lower_bound.astype("float64"),
        "conformal_upper": conf_intervals.upper_bound.astype("float64"),
        "uncertainty_score": composite_u.astype("float64"),
        "uncertainty_method": f"composite (ens:{weights_used['ensemble']:.2f}, ood:{weights_used['ood']:.2f}, conf:{weights_used['conformal']:.2f})",
        "model_version": merged["model_version"].astype("string"),
        "split_strategy": split_strategy,
    })

    # Save uncertainty parquet
    out_unc.parent.mkdir(parents=True, exist_ok=True)
    unc_df.to_parquet(out_unc, engine="pyarrow", index=False)
    print(f"Successfully saved uncertainty estimates to: {out_unc}")

    # 6. Execute Gate-0 Validation Experiment on held-out test data
    eval_mask = test_mask if test_mask.any() else (val_mask if val_mask.any() else ~train_mask)
    if not eval_mask.any():
        eval_mask = np.ones(len(merged), dtype=bool)

    y_eval_true = merged.loc[eval_mask, target_col].values.astype(float)
    y_eval_pred = merged.loc[eval_mask, "prediction"].values.astype(float)
    u_eval = composite_u[eval_mask]

    print("Evaluating Gate-0 uncertainty vs prediction error correlation...")
    gate0_report = evaluate_gate0(
        y_true=y_eval_true,
        y_pred=y_eval_pred,
        uncertainty_scores=u_eval,
        dataset_name=Path(data_file).stem,
        split_strategy=split_strategy,
        uncertainty_method=f"composite (ens={weights_used['ensemble']:.2f}, ood={weights_used['ood']:.2f}, conf={weights_used['conformal']:.2f})",
        is_synthetic_fixture=is_synthetic,
    )

    gate0_report.save_json(out_g0_json)
    gate0_report.save_markdown(out_g0_md)
    print(f"Saved Gate-0 reports to {out_g0_json} and {out_g0_md}")
    print(f"Gate 0 Decision: {'PASSED' if gate0_report.useful_signal else 'WEAK/NO SIGNAL'} (Spearman rho: {gate0_report.spearman_correlation})")

    return unc_df, gate0_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate uncertainty and execute Gate-0 assessment.")
    parser.add_argument("--variants", default="data/curated/variants.parquet", help="Variants parquet path")
    parser.add_argument("--predictions", default="protein_ai/predictions.parquet", help="Predictions parquet path")
    parser.add_argument("--output", default="uncertainty/uncertainty.parquet", help="Uncertainty output parquet path")
    parser.add_argument("--split-strategy", default="mutation_complexity", help="Split strategy")
    args = parser.parse_args()

    print("Running Uncertainty and Gate-0 Evaluation...")
    try:
        run_uncertainty_evaluation(
            variants_parquet=args.variants,
            predictions_parquet=args.predictions,
            output_uncertainty_path=args.output,
            split_strategy=args.split_strategy,
        )
    except FileNotFoundError as e:
        print(f"\n[EVALUATION PAUSED]: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR]: Uncertainty evaluation failed: {e}")
        sys.exit(1)
