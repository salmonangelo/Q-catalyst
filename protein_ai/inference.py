"""Inference and model training pipeline for Protein-AI."""

import argparse
from pathlib import Path
import sys
from typing import Dict, Optional, Tuple
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
from protein_ai.mutation_scoring import MutationScorer
from protein_ai.outputs import save_predictions_parquet
from protein_ai.predictors import FitnessPredictor
from protein_ai.utils import compute_regression_metrics


def run_protein_ai_pipeline(
    variants_parquet: Optional[Path | str] = None,
    output_predictions_path: Optional[Path | str] = None,
    split_manifest_path: Optional[Path | str] = None,
    split_strategy: str = "mutation_complexity",
    protein_ai_config: Optional[ProteinAIConfig] = None,
    global_config: Optional[QCatalystConfig] = None,
) -> Tuple[pd.DataFrame, Dict[str, Dict]]:
    """Execute end-to-end protein AI representation, training, and prediction workflow.

    Args:
        variants_parquet: Path to curated variants parquet.
        output_predictions_path: Destination for predictions.parquet.
        split_manifest_path: Optional path to precomputed split JSON.
        split_strategy: Strategy to use if split manifest path not provided.
        protein_ai_config: ProteinAIConfig instance.
        global_config: QCatalystConfig instance.

    Returns:
        Tuple of (predictions_dataframe, metrics_by_split_dict).
    """
    g_cfg = global_config or load_config()
    p_cfg = protein_ai_config or ProteinAIConfig()

    data_file = Path(variants_parquet or g_cfg.paths.curated_variants_file)
    out_file = Path(output_predictions_path or g_cfg.downstream_contracts.protein_ai)

    if not data_file.exists():
        raise FileNotFoundError(
            f"Curated variants dataset not found at '{data_file}'.\n"
            "Please run 'python data/build_dataset.py' with raw benchmark data first."
        )

    print(f"Loading curated variants from: {data_file}")
    df = pd.read_parquet(data_file)
    if df.empty:
        raise ValueError("Curated variants dataset is empty.")

    # 1. Determine data partition splits
    splitter = DatasetSplitter(config=g_cfg)
    if split_manifest_path and Path(split_manifest_path).exists():
        import json
        with open(split_manifest_path, "r", encoding="utf-8") as f:
            manifest_dict = json.load(f)
        manifest = SplitManifest(**manifest_dict)
        print(f"Loaded existing split manifest ({manifest.strategy}) with {manifest.train_count} train, {manifest.val_count} val, {manifest.test_count} test.")
    else:
        try:
            manifest = splitter.split(df, strategy=split_strategy)
            print(f"Constructed '{split_strategy}' split with {manifest.train_count} train, {manifest.val_count} val, {manifest.test_count} test.")
        except Exception as e:
            print(f"Warning: Grouped split failed ({e}), falling back to random split.")
            manifest = splitter.split(df, strategy="random")

    train_ids = set(manifest.train_variant_ids)
    val_ids = set(manifest.val_variant_ids)
    test_ids = set(manifest.test_variant_ids)

    # Assign split labels
    df["split"] = "unassigned"
    df.loc[df["variant_id"].isin(train_ids), "split"] = "train"
    df.loc[df["variant_id"].isin(val_ids), "split"] = "val"
    df.loc[df["variant_id"].isin(test_ids), "split"] = "test"

    # 2. Extract features
    print("Extracting ESM embeddings and zero-shot mutation scores...")
    feature_pipeline = FeaturePipeline(
        embedding_extractor=EmbeddingExtractor(config=p_cfg.esm),
        mutation_scorer=MutationScorer(config=p_cfg.esm),
        normalize_features=p_cfg.predictor.normalize_features,
    )

    train_df = df[df["split"] == "train"].copy()
    if len(train_df) == 0:
        raise ValueError("No training samples found in dataset split.")

    X_train, train_var_ids = feature_pipeline.fit_transform(train_df)
    X_all, all_var_ids = feature_pipeline.transform(df)

    # 3. Fit lightweight supervised model
    target_col = p_cfg.predictor.target_column
    if target_col not in df.columns or df[target_col].isna().all():
        print(f"Warning: Target column '{target_col}' missing or empty. Falling back to 'activity_value'.")
        target_col = "activity_value"

    y_train = train_df[target_col].values.astype(float)

    predictor = FitnessPredictor(config=p_cfg.predictor)
    predictor.fit(
        X_train=X_train,
        y_train=y_train,
        split_strategy=manifest.strategy,
    )

    # Save model artifact
    predictor.save(output_dir=p_cfg.predictor.artifacts_dir, model_tag=f"activity_{predictor.config.model_type}")

    # 4. Generate predictions for all samples
    preds_all = predictor.predict(X_all)
    score_df = feature_pipeline.mutation_scorer.score_dataframe(df)

    pred_records = []
    for idx, row in df.iterrows():
        var_id = str(row["variant_id"])
        pred_val = float(preds_all[idx])
        mut_score = float(score_df.loc[idx, "mutation_score"])

        pred_records.append({
            "variant_id": var_id,
            "prediction": pred_val,
            "zero_shot_score": mut_score,
            "esm_log_likelihood_ratio": mut_score,
            "model_name": feature_pipeline.embedding_extractor.model.model_name,
            "model_version": f"{predictor.config.model_type}_v1.0",
            "split": str(row["split"]),
            "prediction_target": target_col,
        })

    pred_df = pd.DataFrame(pred_records)
    save_predictions_parquet(pred_df, output_path=out_file)
    print(f"Saved {len(pred_df)} predictions to: {out_file}")

    # 5. Compute evaluation metrics
    metrics_by_split = {}
    for split_name in ["train", "val", "test"]:
        split_mask = df["split"] == split_name
        if split_mask.any():
            y_t = df.loc[split_mask, target_col].values.astype(float)
            y_p = preds_all[split_mask]
            metrics = compute_regression_metrics(y_t, y_p)
            metrics_by_split[split_name] = metrics
            print(
                f"[{split_name.upper()} Metrics] N={metrics['n_samples']} | "
                f"Spearman: {metrics.get('spearman_rho')} | MAE: {metrics.get('mae')} | RMSE: {metrics.get('rmse')}"
            )

    return pred_df, metrics_by_split


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Protein-AI feature and inference pipeline.")
    parser.add_argument("--variants", default="data/curated/variants.parquet", help="Curated variants parquet path")
    parser.add_argument("--output", default="protein_ai/predictions.parquet", help="Predictions output path")
    parser.add_argument("--split-strategy", default="mutation_complexity", help="Dataset splitting strategy")
    args = parser.parse_args()

    print("Running Protein-AI Inference Pipeline...")
    try:
        run_protein_ai_pipeline(
            variants_parquet=args.variants,
            output_predictions_path=args.output,
            split_strategy=args.split_strategy,
        )
    except FileNotFoundError as e:
        print(f"\n[PIPELINE PAUSED]: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR]: Pipeline failed: {e}")
        sys.exit(1)
