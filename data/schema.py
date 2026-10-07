"""Canonical variant schema and Pydantic models for Q-Catalyst."""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator

from data.mutations import CANONICAL_AMINO_ACIDS, normalize_mutation_string, parse_mutations


# Canonical column names in exact order
CANONICAL_COLUMNS: List[str] = [
    "variant_id",
    "parent_enzyme",
    "sequence",
    "mutations",
    "activity_value",
    "activity_unit",
    "activity_rel_to_parent",
    "Tm_C",
    "dTm_vs_parent",
    "temperature_C",
    "pH",
    "substrate",
    "PET_crystallinity_pct",
    "enzyme_loading",
    "reaction_time",
    "assay_method",
    "product_measured",
    "publication",
    "patent_flag",
    "data_quality_flag",
    "study_id",
]

# Column data type mapping for pyarrow parquet persistence
COLUMN_DTYPES: Dict[str, str] = {
    "variant_id": "string",
    "parent_enzyme": "string",
    "sequence": "string",
    "mutations": "string",
    "activity_value": "float64",
    "activity_unit": "string",
    "activity_rel_to_parent": "float64",
    "Tm_C": "float64",
    "dTm_vs_parent": "float64",
    "temperature_C": "float64",
    "pH": "float64",
    "substrate": "string",
    "PET_crystallinity_pct": "float64",
    "enzyme_loading": "string",
    "reaction_time": "string",
    "assay_method": "string",
    "product_measured": "string",
    "publication": "string",
    "patent_flag": "boolean",
    "data_quality_flag": "string",
    "study_id": "string",
}


class VariantRecord(BaseModel):
    """Pydantic model representing a single canonical variant entry."""
    model_config = ConfigDict(extra="ignore")

    variant_id: str = Field(..., description="Unique variant identifier")
    parent_enzyme: str = Field(..., description="Parent wild-type enzyme name (e.g. IsPETase)")
    sequence: str = Field(..., description="Full amino acid sequence")
    mutations: str = Field(default="WT", description="Canonical mutation string (e.g. S160A;D206G or WT)")

    activity_value: Optional[float] = Field(default=None, description="Raw measured activity value")
    activity_unit: Optional[str] = Field(default=None, description="Unit for activity_value")
    activity_rel_to_parent: Optional[float] = Field(default=None, description="Fold-change relative to WT (WT=1.0)")
    Tm_C: Optional[float] = Field(default=None, description="Melting temperature in deg C")
    dTm_vs_parent: Optional[float] = Field(default=None, description="Change in Tm vs parent in deg C")
    temperature_C: Optional[float] = Field(default=None, description="Assay temperature in deg C")
    pH: Optional[float] = Field(default=None, description="Assay pH")
    substrate: Optional[str] = Field(default=None, description="PET substrate type")
    PET_crystallinity_pct: Optional[float] = Field(default=None, description="Crystallinity percentage (0-100)")
    enzyme_loading: Optional[str] = Field(default=None, description="Assay enzyme loading")
    reaction_time: Optional[str] = Field(default=None, description="Assay reaction duration")
    assay_method: Optional[str] = Field(default=None, description="Assay detection method")
    product_measured: Optional[str] = Field(default=None, description="Specific reaction product quantified")
    publication: Optional[str] = Field(default=None, description="Literature citation or DOI")
    patent_flag: Optional[bool] = Field(default=False, description="Whether data originates from patent literature")
    data_quality_flag: Optional[str] = Field(default="PASS", description="Data curation quality assessment flag")
    study_id: Optional[str] = Field(default=None, description="Study or dataset grouping identifier")

    @field_validator("sequence")
    @classmethod
    def validate_sequence(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Sequence cannot be empty")
        invalid_chars = set(cleaned) - CANONICAL_AMINO_ACIDS
        if invalid_chars:
            raise ValueError(f"Sequence contains non-canonical characters: {sorted(invalid_chars)}")
        return cleaned

    @field_validator("mutations")
    @classmethod
    def validate_mutations(cls, v: Optional[str]) -> str:
        return normalize_mutation_string(v)

    @field_validator("PET_crystallinity_pct")
    @classmethod
    def validate_crystallinity(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError(f"PET crystallinity % must be between 0 and 100, got {v}")
        return v

    @field_validator("pH")
    @classmethod
    def validate_ph(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 14.0):
            raise ValueError(f"pH must be between 0 and 14, got {v}")
        return v


def enforce_canonical_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce exact canonical column order, presence, and types on a DataFrame.

    Missing optional columns will be initialized with appropriate NaN/None.

    Args:
        df: Input DataFrame.

    Returns:
        Standardized DataFrame with CANONICAL_COLUMNS.
    """
    df_out = df.copy()

    # Ensure all canonical columns exist
    for col in CANONICAL_COLUMNS:
        if col not in df_out.columns:
            df_out[col] = None

    # Reorder to canonical layout
    df_out = df_out[CANONICAL_COLUMNS].copy()

    # Enforce type coercions safely
    for col, dtype in COLUMN_DTYPES.items():
        if dtype == "string":
            df_out[col] = df_out[col].astype("string")
        elif dtype == "float64":
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce").astype("float64")
        elif dtype == "boolean":
            df_out[col] = df_out[col].astype("boolean")

    return df_out
