"""Output schema and file persistence for Protein-AI predictions."""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


PREDICTION_COLUMNS: List[str] = [
    "variant_id",
    "prediction",
    "zero_shot_score",
    "esm_log_likelihood_ratio",
    "model_name",
    "model_version",
    "split",
    "prediction_target",
]

PREDICTION_DTYPES: Dict[str, str] = {
    "variant_id": "string",
    "prediction": "float64",
    "zero_shot_score": "float64",
    "esm_log_likelihood_ratio": "float64",
    "model_name": "string",
    "model_version": "string",
    "split": "string",
    "prediction_target": "string",
}


def enforce_predictions_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure prediction DataFrame conforms strictly to registered schema."""
    df_out = df.copy()
    for col in PREDICTION_COLUMNS:
        if col not in df_out.columns:
            df_out[col] = None

    df_out = df_out[PREDICTION_COLUMNS].copy()

    for col, dtype in PREDICTION_DTYPES.items():
        if dtype == "string":
            df_out[col] = df_out[col].astype("string")
        elif dtype == "float64":
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce").astype("float64")

    return df_out


def save_predictions_parquet(
    df: pd.DataFrame,
    output_path: Path | str = "protein_ai/predictions.parquet"
) -> Path:
    """Save validated predictions DataFrame as Parquet."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    canonical = enforce_predictions_schema(df)
    canonical.to_parquet(p, engine="pyarrow", index=False)
    return p
