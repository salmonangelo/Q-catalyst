"""CLI orchestrator for Smart Acquisition Gate candidate selection."""

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple
import pandas as pd

# Ensure project root in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from acquisition.config import AcquisitionConfig
from acquisition.outputs import save_acquisition_outputs
from acquisition.selector import SelectedCandidate, SmartAcquisitionSelector
from configs.config_schema import QCatalystConfig, load_config
from protein_ai.embeddings import EmbeddingExtractor


def run_acquisition_pipeline(
    predictions_parquet: Optional[Path | str] = None,
    uncertainty_parquet: Optional[Path | str] = None,
    variants_parquet: Optional[Path | str] = None,
    gate0_json_path: Optional[Path | str] = None,
    output_jobs_json: Optional[Path | str] = None,
    output_candidates_parquet: Optional[Path | str] = None,
    acquisition_config: Optional[AcquisitionConfig] = None,
    global_config: Optional[QCatalystConfig] = None,
    is_synthetic_run: bool = False,
) -> Tuple[List[SelectedCandidate], Dict]:
    """Execute Smart Acquisition Gate candidate selection pipeline.

    Args:
        predictions_parquet: Path to predictions.parquet.
        uncertainty_parquet: Path to uncertainty.parquet.
        variants_parquet: Path to variants.parquet.
        gate0_json_path: Path to gate0_report.json.
        output_jobs_json: Destination for chem_jobs.json.
        output_candidates_parquet: Destination for selected_candidates.parquet.
        acquisition_config: AcquisitionConfig instance.
        global_config: QCatalystConfig instance.
        is_synthetic_run: Whether running on test fixture.

    Returns:
        Tuple of (selected_candidates_list, summary_metadata).
    """
    g_cfg = global_config or load_config()
    a_cfg = acquisition_config or AcquisitionConfig()

    pred_file = Path(predictions_parquet or g_cfg.downstream_contracts.protein_ai)
    unc_file = Path(uncertainty_parquet or g_cfg.downstream_contracts.uncertainty)
    var_file = Path(variants_parquet or g_cfg.paths.curated_variants_file)
    g0_file = Path(gate0_json_path or "uncertainty/gate0_report.json")

    out_json = Path(output_jobs_json or a_cfg.output_jobs_json)
    out_pq = Path(output_candidates_parquet or a_cfg.output_candidates_parquet)

    # Validate input presence
    if not pred_file.exists():
        raise FileNotFoundError(
            f"Predictions file not found at '{pred_file}'.\n"
            "Please run 'python -m protein_ai.inference' first."
        )

    if not unc_file.exists():
        raise FileNotFoundError(
            f"Uncertainty file not found at '{unc_file}'.\n"
            "Please run 'python -m uncertainty.evaluate' first."
        )

    print(f"Loading predictions from: {pred_file}")
    df_preds = pd.read_parquet(pred_file)
    print(f"Loading uncertainty from: {unc_file}")
    df_unc = pd.read_parquet(unc_file)

    # Merge inputs
    merged = pd.merge(
        df_preds,
        df_unc[["variant_id", "uncertainty_score", "ensemble_std", "ood_score", "conformal_lower", "conformal_upper"]],
        on="variant_id",
        how="inner",
    )

    if var_file.exists():
        df_var = pd.read_parquet(var_file)
        # Add parent_enzyme and mutations if available
        cols_to_add = [c for c in ["parent_enzyme", "mutations", "sequence", "data_quality_flag"] if c in df_var.columns]
        merged = pd.merge(merged, df_var[["variant_id"] + cols_to_add], on="variant_id", how="left")

    if "parent_enzyme" not in merged.columns:
        merged["parent_enzyme"] = "IsPETase"
    if "mutations" not in merged.columns:
        merged["mutations"] = "WT"

    # Inspect Gate-0 validation status
    gate0_validated = False
    gate0_reason = "Gate-0 report not found."

    if g0_file.exists():
        try:
            with open(g0_file, "r", encoding="utf-8") as f:
                g0_data = json.load(f)
            gate0_validated = bool(g0_data.get("useful_signal", False))
            is_synthetic_fixture = any("TEST RUN ONLY" in lim for lim in g0_data.get("limitations", []))
            if is_synthetic_fixture and not is_synthetic_run:
                gate0_validated = False
                gate0_reason = "Gate-0 only evaluated on synthetic test fixture, not real empirical benchmark data."
            elif gate0_validated:
                gate0_reason = f"Gate-0 empirically confirmed uncertainty usefulness (Spearman rho={g0_data.get('spearman_correlation')})."
            else:
                gate0_reason = f"Gate-0 showed weak/no correlation with prediction error ({g0_data.get('signal_strength')})."
        except Exception as e:
            gate0_reason = f"Failed to parse Gate-0 report: {e}"

    print(f"Gate-0 Status: {'VALIDATED' if gate0_validated else 'UNVALIDATED'} ({gate0_reason})")

    # Extract sequence embeddings if available
    embeddings = None
    if "sequence" in merged.columns and merged["sequence"].notna().all():
        try:
            extractor = EmbeddingExtractor()
            embeddings, _ = extractor.embed_dataframe(merged)
        except Exception as e:
            print(f"Note: Could not extract embeddings for diversity ({e}); using mutation token distance.")
            embeddings = None

    # Run Smart Acquisition Selector
    selector = SmartAcquisitionSelector(config=a_cfg)
    selected_candidates, summary_meta = selector.select_candidates(
        df_candidates=merged,
        embeddings=embeddings,
        gate0_validated=gate0_validated,
    )

    # Save outputs
    save_acquisition_outputs(
        selected_candidates=selected_candidates,
        summary_metadata=summary_meta,
        output_json_path=out_json,
        output_parquet_path=out_pq,
        dataset_name=Path(pred_file).stem,
        split_strategy=summary_meta.get("active_strategy", "mechanism_aware"),
    )

    print(f"\nSuccessfully selected {len(selected_candidates)} candidates for chemistry modeling.")
    print(f"Outputs written to:\n - {out_json}\n - {out_pq}")

    # Print summary table
    print("\n" + "=" * 80)
    print("PHASE 3: SMART ACQUISITION SELECTION SUMMARY")
    print("=" * 80)
    for c in selected_candidates:
        print(f"Rank #{c.selection_rank:02d} | Variant: {c.variant_id:<25} | Pred: {c.predicted_performance:.2f} | Unc: {c.uncertainty if c.uncertainty is not None else 0.0:.2f} | Prox: {c.proximity_score if c.proximity_score is not None else 0.0:.2f} | Score: {c.acquisition_score:.3f}")
        print(f"  Reason: {c.selection_reason}")
    print("=" * 80 + "\n")

    return selected_candidates, summary_meta


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Smart Acquisition Gate selection.")
    parser.add_argument("--predictions", default="protein_ai/predictions.parquet", help="Predictions parquet path")
    parser.add_argument("--uncertainty", default="uncertainty/uncertainty.parquet", help="Uncertainty parquet path")
    parser.add_argument("--variants", default="data/curated/variants.parquet", help="Curated variants path")
    parser.add_argument("--gate0", default="uncertainty/gate0_report.json", help="Gate 0 report JSON path")
    parser.add_argument("--budget", type=int, default=10, help="Chemistry candidate budget")
    parser.add_argument("--strategy", default="mechanism_aware", help="Acquisition strategy")
    parser.add_argument("--synthetic-run", action="store_true", help="Explicitly mark run as synthetic test")
    args = parser.parse_args()

    cfg = AcquisitionConfig(chemistry_budget=args.budget, strategy=args.strategy)

    print("Executing Smart Acquisition Gate...")
    try:
        run_acquisition_pipeline(
            predictions_parquet=args.predictions,
            uncertainty_parquet=args.uncertainty,
            variants_parquet=args.variants,
            gate0_json_path=args.gate0,
            acquisition_config=cfg,
            is_synthetic_run=args.synthetic_run,
        )
    except FileNotFoundError as e:
        print(f"\n[ACQUISITION PAUSED]: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR]: Acquisition pipeline failed: {e}")
        sys.exit(1)
