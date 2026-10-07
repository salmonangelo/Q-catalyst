import json
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

# Ensure project root is in sys.path when executed directly
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd

from configs.config_schema import QCatalystConfig, load_config
from data.mutations import (
    MutationParseError,
    SequenceMismatchError,
    apply_mutations_to_sequence,
    normalize_mutation_string,
    parse_mutations,
)
from data.schema import CANONICAL_COLUMNS, enforce_canonical_schema
from data.validate import validate_dataframe

# Well-characterized PETase Wild-Type Reference Sequences (signal peptide cleaved where standard)
REFERENCE_PARENT_SEQUENCES: Dict[str, str] = {
    # IsPETase (Ideonella sakaiensis 201-F6 PETase, mature enzyme sequence 28-290, 263 AA)
    "IsPETase": (
        "QTNPYARGPNPTAASLEASAGPFTVRSFTVSRPSGYGAGTVYYPTNAGGTVGAIAIVPGYTARQSSIKWWGPR"
        "LASHGFVVITIDTNSTLDQPSSRSSQQMAALRQVASLNGTSSSPIYGKVDTARMGVMGWSMGGGGSLISAANN"
        "PSLRAAIPQAPWDSSTNFSSVTVPTLIFACENDSIAPVNSSALPIYDSMSRNAKQFLEINGGSHSCANSGNSN"
        "QALIGKKGVAWMKRFMDNDTRYSTFACENPNSTRVSDFRTANCS"
    ),
    # LCC (Leaf-branch compost cutinase, 258 AA)
    "LCC": (
        "SNPWDPFRAPNTSSSQLEAYSLGPREYTVRTYSVSRPSGWGDGTVTYPTNSTGTIGAIAVIPGYSVRSNSISWW"
        "GPRLASHGFVVITIDTNSTLDQPSARSSQQLAALQQVAASLGGTASTPIYGKVDTARMGVMGWSMGGGGSLISA"
        "ANSPSLRAAIPQAPWDSSTNFSSVTVPTLIFACENDSIAPVNSSALPIYDSMSRNAKQFLEINGGSHSCANSGN"
        "SNQALIGKKGVAWMKRFMDNDTRYSTFACENPNSTRVSDFRTANCS"
    ),
}

# Standard column mapping dictionary for common raw benchmark formats (e.g. PET-Gym / literature tables)
RAW_COLUMN_ALIASES: Dict[str, str] = {
    "variant": "variant_id",
    "id": "variant_id",
    "mutant_id": "variant_id",
    "name": "variant_id",
    "parent": "parent_enzyme",
    "wild_type": "parent_enzyme",
    "wt": "parent_enzyme",
    "seq": "sequence",
    "aa_sequence": "sequence",
    "mutant_sequence": "sequence",
    "mutation": "mutations",
    "muts": "mutations",
    "mutant": "mutations",
    "substitutions": "mutations",
    "fitness": "activity_rel_to_parent",
    "score": "activity_rel_to_parent",
    "activity": "activity_value",
    "rel_activity": "activity_rel_to_parent",
    "relative_activity": "activity_rel_to_parent",
    "fold_change": "activity_rel_to_parent",
    "tm": "Tm_C",
    "melting_temperature": "Tm_C",
    "dtm": "dTm_vs_parent",
    "temp": "temperature_C",
    "temp_c": "temperature_C",
    "assay_temp": "temperature_C",
    "ph_val": "pH",
    "crystallinity": "PET_crystallinity_pct",
    "cryst_pct": "PET_crystallinity_pct",
    "doi": "publication",
    "paper": "publication",
    "study": "study_id",
    "dataset": "study_id",
    "source": "study_id",
}


def normalize_raw_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names according to alias mapping."""
    rename_dict = {}
    for col in df.columns:
        clean_col = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        if clean_col in RAW_COLUMN_ALIASES:
            rename_dict[col] = RAW_COLUMN_ALIASES[clean_col]
        elif clean_col in CANONICAL_COLUMNS:
            rename_dict[col] = clean_col
    return df.rename(columns=rename_dict)


def curate_variant_records(
    raw_df: pd.DataFrame,
    default_parent: str = "IsPETase",
    default_study_id: str = "PET-Gym",
    reference_sequences: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Transform raw benchmark DataFrame into canonical curated variants format.

    Args:
        raw_df: Raw input DataFrame.
        default_parent: Default parent enzyme if not specified.
        default_study_id: Default study ID if not specified.
        reference_sequences: Dict mapping parent name -> wild-type AA sequence.

    Returns:
        Curated canonical DataFrame with data_quality_flag.
    """
    ref_seqs = reference_sequences or REFERENCE_PARENT_SEQUENCES
    df = normalize_raw_columns(raw_df)

    curated_rows: List[Dict] = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()

        # 1. Determine parent enzyme
        parent = row_dict.get("parent_enzyme")
        if pd.isna(parent) or not str(parent).strip():
            parent = default_parent
        parent = str(parent).strip()

        # 2. Determine mutations
        mut_raw = row_dict.get("mutations")
        norm_muts = "WT"
        parsed_muts = []
        try:
            parsed_muts = parse_mutations(str(mut_raw) if pd.notna(mut_raw) else None)
            norm_muts = normalize_mutation_string(str(mut_raw) if pd.notna(mut_raw) else None)
        except MutationParseError as e:
            # Keep raw if cannot parse, flag quality
            norm_muts = str(mut_raw) if pd.notna(mut_raw) else "UNKNOWN"

        # 3. Determine sequence
        seq = row_dict.get("sequence")
        quality_flag = "PASS"

        if pd.isna(seq) or not str(seq).strip():
            # If sequence missing, attempt reconstruction from parent reference sequence
            if parent in ref_seqs:
                ref_seq = ref_seqs[parent]
                if norm_muts == "WT":
                    seq = ref_seq
                    quality_flag = "PASS_WT_REFERENCE"
                else:
                    try:
                        seq = apply_mutations_to_sequence(ref_seq, parsed_muts, offset=1, strict_wt_check=True)
                        quality_flag = "PASS_RECONSTRUCTED_SEQUENCE"
                    except (SequenceMismatchError, ValueError) as err:
                        quality_flag = f"WARNING_SEQUENCE_RECONSTRUCTION_FAILED: {err}"
                        seq = None
            else:
                quality_flag = f"WARNING_MISSING_SEQUENCE_NO_PARENT_REF_{parent}"
                seq = None
        else:
            seq = str(seq).strip().upper()

        # 4. Determine variant_id
        var_id = row_dict.get("variant_id")
        if pd.isna(var_id) or not str(var_id).strip():
            if norm_muts == "WT":
                var_id = f"{parent}_WT"
            else:
                var_id = f"{parent}_{norm_muts.replace(';', '_')}"
        var_id = str(var_id).strip()

        # 5. Determine study_id
        study_id = row_dict.get("study_id")
        if pd.isna(study_id) or not str(study_id).strip():
            study_id = default_study_id
        study_id = str(study_id).strip()

        # Construct curated dictionary
        curated_entry = {
            "variant_id": var_id,
            "parent_enzyme": parent,
            "sequence": seq,
            "mutations": norm_muts,
            "activity_value": row_dict.get("activity_value"),
            "activity_unit": row_dict.get("activity_unit"),
            "activity_rel_to_parent": row_dict.get("activity_rel_to_parent"),
            "Tm_C": row_dict.get("Tm_C"),
            "dTm_vs_parent": row_dict.get("dTm_vs_parent"),
            "temperature_C": row_dict.get("temperature_C"),
            "pH": row_dict.get("pH"),
            "substrate": row_dict.get("substrate"),
            "PET_crystallinity_pct": row_dict.get("PET_crystallinity_pct"),
            "enzyme_loading": str(row_dict["enzyme_loading"]) if pd.notna(row_dict.get("enzyme_loading")) else None,
            "reaction_time": str(row_dict["reaction_time"]) if pd.notna(row_dict.get("reaction_time")) else None,
            "assay_method": row_dict.get("assay_method"),
            "product_measured": row_dict.get("product_measured"),
            "publication": row_dict.get("publication"),
            "patent_flag": bool(row_dict.get("patent_flag", False)) if pd.notna(row_dict.get("patent_flag")) else False,
            "data_quality_flag": quality_flag,
            "study_id": study_id,
        }

        curated_rows.append(curated_entry)

    curated_df = pd.DataFrame(curated_rows)
    return enforce_canonical_schema(curated_df)


def build_curated_dataset(
    raw_data_dir: Optional[Path | str] = None,
    output_parquet: Optional[Path | str] = None,
    output_report: Optional[Path | str] = None,
    config: Optional[QCatalystConfig] = None,
) -> Tuple[pd.DataFrame, Dict]:
    """Discover raw files in data/raw/, curate into canonical schema, validate, and write parquet.

    Fails cleanly if raw data directory is empty or raw files are missing.

    Args:
        raw_data_dir: Directory containing raw benchmark files.
        output_parquet: Path to write curated variants.parquet.
        output_report: Path to write data_quality_report.json.
        config: QCatalyst configuration object.

    Returns:
        Tuple of (curated DataFrame, quality report dictionary).
    """
    cfg = config or load_config()
    raw_dir = Path(raw_data_dir or cfg.paths.raw_data_dir)
    out_pq = Path(output_parquet or cfg.paths.curated_variants_file)
    out_rpt = Path(output_report or cfg.paths.quality_report_file)

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory does not exist at: {raw_dir}")

    # Discover raw tabular files (csv, parquet, tsv)
    raw_files = [
        f for f in raw_dir.glob("*") if f.suffix.lower() in (".csv", ".parquet", ".tsv", ".json")
    ]

    if not raw_files:
        raise FileNotFoundError(
            f"No raw dataset files found in {raw_dir}.\n"
            f"Expected benchmark files (e.g. PET-Gym datasets or literature tables).\n"
            f"Please place raw files into '{raw_dir}' or run 'python scripts/download_petgym.py' for instructions."
        )

    print(f"Found {len(raw_files)} raw data source(s) in {raw_dir}: {[f.name for f in raw_files]}")

    dfs = []
    for f in sorted(raw_files):
        print(f"Loading raw file: {f.name}")
        if f.suffix.lower() == ".parquet":
            raw_sub_df = pd.read_parquet(f)
        elif f.suffix.lower() == ".json":
            raw_sub_df = pd.read_json(f)
        else:
            sep = "\t" if f.suffix.lower() == ".tsv" else ","
            raw_sub_df = pd.read_csv(f, sep=sep)

        curated_sub_df = curate_variant_records(
            raw_sub_df,
            default_parent=cfg.structure.reference_parent,
            default_study_id=f.stem,
        )
        dfs.append(curated_sub_df)

    combined_df = pd.concat(dfs, ignore_index=True)
    # Deduplicate exact matching variant_ids if present across identical files
    combined_df = combined_df.drop_duplicates(subset=["variant_id"], keep="first")
    canonical_df = enforce_canonical_schema(combined_df)

    # Validate curated dataset
    report = validate_dataframe(
        canonical_df, config=cfg, parent_reference_sequences=REFERENCE_PARENT_SEQUENCES
    )

    # Ensure output directories exist
    out_pq.parent.mkdir(parents=True, exist_ok=True)
    canonical_df.to_parquet(out_pq, engine="pyarrow", index=False)
    print(f"Successfully saved {len(canonical_df)} curated records to {out_pq}")

    report.save_json(out_rpt)
    print(f"Saved quality report to {out_rpt} (Passed: {report.passed}, Errors: {report.error_count}, Warnings: {report.warning_count})")

    return canonical_df, report.to_dict()


if __name__ == "__main__":
    import sys

    print("Executing Q-Catalyst dataset build pipeline...")
    try:
        df, rpt = build_curated_dataset()
        print(f"Build complete. Total variants: {len(df)}")
    except FileNotFoundError as e:
        print(f"\n[DATASET BUILD PAUSED]: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR]: Failed to build curated dataset: {e}")
        sys.exit(1)
