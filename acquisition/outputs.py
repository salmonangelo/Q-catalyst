"""Output serialization for acquisition contracts (chem_jobs.json and selected_candidates.parquet)."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from acquisition.selector import SelectedCandidate


SELECTED_CANDIDATE_COLUMNS = [
    "job_id",
    "variant_id",
    "parent_enzyme",
    "mutations",
    "predicted_performance",
    "uncertainty",
    "proximity_score",
    "diversity_score",
    "estimated_chemistry_cost",
    "acquisition_score",
    "selection_rank",
    "selection_reason",
    "structure_mapping_status",
]


def save_acquisition_outputs(
    selected_candidates: List[SelectedCandidate],
    summary_metadata: Dict[str, Any],
    output_json_path: Path | str = "acquisition/chem_jobs.json",
    output_parquet_path: Path | str = "acquisition/selected_candidates.parquet",
    dataset_name: str = "curated_variants",
    split_strategy: str = "mutation_complexity",
) -> Tuple[Path, Path]:
    """Serialize selected candidate list to chem_jobs.json and selected_candidates.parquet.

    Args:
        selected_candidates: List of SelectedCandidate objects.
        summary_metadata: Metadata dictionary from selector.
        output_json_path: Destination JSON path.
        output_parquet_path: Destination Parquet path.
        dataset_name: Name of underlying dataset.
        split_strategy: Split strategy used.

    Returns:
        Tuple of (saved_json_path, saved_parquet_path).
    """
    json_path = Path(output_json_path)
    parquet_path = Path(output_parquet_path)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Build structured candidates list with job_ids
    candidates_list: List[Dict[str, Any]] = []
    rows_for_df: List[Dict[str, Any]] = []

    for c in selected_candidates:
        job_id = f"chem_job_{c.selection_rank:03d}"
        c_dict = c.to_dict()
        c_dict["job_id"] = job_id
        c_dict["active_site_residues"] = [160, 206, 237, 87, 161, 185, 159]
        c_dict["qm_method_requested"] = "CASCI_VQE_CLUSTER_TRIAD"

        candidates_list.append(c_dict)

        row = {
            "job_id": job_id,
            "variant_id": str(c.variant_id),
            "parent_enzyme": str(c.parent_enzyme),
            "mutations": str(c.mutations),
            "predicted_performance": float(c.predicted_performance),
            "uncertainty": float(c.uncertainty) if c.uncertainty is not None else None,
            "proximity_score": float(c.proximity_score) if c.proximity_score is not None else None,
            "diversity_score": float(c.diversity_score),
            "estimated_chemistry_cost": str(c.estimated_chemistry_cost),
            "acquisition_score": float(c.acquisition_score),
            "selection_rank": int(c.selection_rank),
            "selection_reason": str(c.selection_reason),
            "structure_mapping_status": str(c.structure_mapping_status),
        }
        rows_for_df.append(row)

    # 2. Build full JSON payload
    gate0_status = (
        "EMPIRICALLY_VALIDATED"
        if summary_metadata.get("gate0_validated")
        else "UNVALIDATED_OR_SYNTHETIC_FIXTURE"
    )

    json_payload = {
        "metadata": {
            "dataset": dataset_name,
            "split_strategy": split_strategy,
            "gate0_status": gate0_status,
            "acquisition_strategy": summary_metadata.get("active_strategy", "mechanism_aware"),
            "budget": summary_metadata.get("requested_budget", 10),
            "selected_count": summary_metadata.get("selected_count", len(selected_candidates)),
            "selection_shortfall": summary_metadata.get("selection_shortfall", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "candidates": candidates_list,
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)

    # 3. Build and save Parquet table
    if rows_for_df:
        df_out = pd.DataFrame(rows_for_df)
    else:
        df_out = pd.DataFrame(columns=SELECTED_CANDIDATE_COLUMNS)

    # Enforce dtypes
    for col in SELECTED_CANDIDATE_COLUMNS:
        if col not in df_out.columns:
            df_out[col] = None

    df_out["job_id"] = df_out["job_id"].astype("string")
    df_out["variant_id"] = df_out["variant_id"].astype("string")
    df_out["parent_enzyme"] = df_out["parent_enzyme"].astype("string")
    df_out["mutations"] = df_out["mutations"].astype("string")
    df_out["predicted_performance"] = df_out["predicted_performance"].astype("float64")
    df_out["uncertainty"] = pd.to_numeric(df_out["uncertainty"], errors="coerce").astype("float64")
    df_out["proximity_score"] = pd.to_numeric(df_out["proximity_score"], errors="coerce").astype("float64")
    df_out["diversity_score"] = df_out["diversity_score"].astype("float64")
    df_out["estimated_chemistry_cost"] = df_out["estimated_chemistry_cost"].astype("string")
    df_out["acquisition_score"] = df_out["acquisition_score"].astype("float64")
    df_out["selection_rank"] = df_out["selection_rank"].astype("int64")
    df_out["selection_reason"] = df_out["selection_reason"].astype("string")
    df_out["structure_mapping_status"] = df_out["structure_mapping_status"].astype("string")

    df_out = df_out[SELECTED_CANDIDATE_COLUMNS].copy()
    df_out.to_parquet(parquet_path, engine="pyarrow", index=False)

    return json_path, parquet_path
