"""Comprehensive data validation module for Q-Catalyst variant datasets."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

from configs.config_schema import QCatalystConfig, load_config
from data.mutations import (
    CANONICAL_AMINO_ACIDS,
    MutationParseError,
    SequenceMismatchError,
    apply_mutations_to_sequence,
    parse_mutations,
)
from data.schema import CANONICAL_COLUMNS


@dataclass
class ValidationIssue:
    """Represents a specific validation finding."""
    severity: str  # 'ERROR', 'WARNING', 'INFO'
    category: str  # e.g., 'SCHEMA', 'SEQUENCE', 'MUTATION', 'NUMERIC', 'DUPLICATE'
    message: str
    row_index: Optional[int] = None
    variant_id: Optional[str] = None


@dataclass
class ValidationReport:
    """Aggregated validation report."""
    total_records: int = 0
    passed: bool = True
    error_count: int = 0
    warning_count: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)

    def add_issue(
        self,
        severity: str,
        category: str,
        message: str,
        row_index: Optional[int] = None,
        variant_id: Optional[str] = None,
    ) -> None:
        severity_upper = severity.upper()
        if severity_upper == "ERROR":
            self.passed = False
            self.error_count += 1
        elif severity_upper == "WARNING":
            self.warning_count += 1

        self.issues.append(
            ValidationIssue(
                severity=severity_upper,
                category=category.upper(),
                message=message,
                row_index=row_index,
                variant_id=variant_id,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "summary_metrics": self.summary_metrics,
            "issues": [asdict(i) for i in self.issues],
        }

    def save_json(self, output_path: Path | str) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


def validate_dataframe(
    df: pd.DataFrame,
    config: Optional[QCatalystConfig] = None,
    parent_reference_sequences: Optional[Dict[str, str]] = None,
) -> ValidationReport:
    """Run full validation suite against a variant DataFrame.

    Checks:
    - empty dataset
    - required columns
    - duplicate variant IDs & duplicate rows
    - valid amino-acid sequences & impossible characters
    - mutation syntax and consistency
    - missing critical values
    - numeric boundary validity
    - parent identifier consistency

    Args:
        df: Input pandas DataFrame.
        config: Optional configuration instance.
        parent_reference_sequences: Optional dict mapping parent_enzyme -> sequence.

    Returns:
        ValidationReport instance.
    """
    if config is None:
        config = load_config()

    report = ValidationReport(total_records=len(df))

    # 1. Empty dataset check
    if df is None or df.empty:
        report.add_issue("ERROR", "EMPTY", "Dataset is completely empty.")
        return report

    # 2. Required columns check
    req_cols = config.dataset.required_columns
    missing_req = [col for col in req_cols if col not in df.columns]
    if missing_req:
        report.add_issue(
            "ERROR", "SCHEMA", f"Missing required columns in dataset: {missing_req}"
        )

    # 3. Duplicate checks
    if "variant_id" in df.columns:
        null_ids = df["variant_id"].isna().sum()
        if null_ids > 0:
            report.add_issue(
                "ERROR", "SCHEMA", f"Found {null_ids} records with missing variant_id."
            )

        dup_ids = df[df["variant_id"].duplicated(keep=False)]
        if not dup_ids.empty:
            dup_id_list = dup_ids["variant_id"].unique().tolist()[:10]
            report.add_issue(
                "ERROR",
                "DUPLICATE",
                f"Duplicate variant_ids detected ({len(dup_ids)} rows affected). Examples: {dup_id_list}",
            )

    # Exact row duplicates
    dup_rows = df.duplicated().sum()
    if dup_rows > 0:
        report.add_issue(
            "WARNING", "DUPLICATE", f"Dataset contains {dup_rows} exact duplicate rows."
        )

    # Sequence + parent duplicates with contradictory activities
    if {"parent_enzyme", "sequence", "activity_rel_to_parent"}.issubset(df.columns):
        grouped = df.groupby(["parent_enzyme", "sequence"])["activity_rel_to_parent"].nunique()
        contradictory = grouped[grouped > 1]
        if not contradictory.empty:
            report.add_issue(
                "WARNING",
                "BIOLOGICAL",
                f"Found {len(contradictory)} sequences with conflicting activity measurements across studies.",
            )

    # 4. Row-level validations
    unique_parents: Set[str] = set()
    single_mut_count = 0
    multi_mut_count = 0
    wt_count = 0

    val_cfg = config.validation

    for idx, row in df.iterrows():
        var_id = str(row.get("variant_id", f"row_{idx}"))

        # Parent enzyme check
        parent = row.get("parent_enzyme")
        if pd.isna(parent) or not str(parent).strip():
            report.add_issue(
                "ERROR", "SCHEMA", "Missing parent_enzyme value.", row_index=idx, variant_id=var_id
            )
        else:
            unique_parents.add(str(parent).strip())

        # Sequence validation
        seq = row.get("sequence")
        if pd.isna(seq) or not str(seq).strip():
            report.add_issue(
                "ERROR", "SEQUENCE", "Sequence is missing or empty.", row_index=idx, variant_id=var_id
            )
        else:
            seq_str = str(seq).strip().upper()
            seq_len = len(seq_str)

            if seq_len < val_cfg.min_sequence_length:
                report.add_issue(
                    "ERROR",
                    "SEQUENCE",
                    f"Sequence length {seq_len} is below minimum ({val_cfg.min_sequence_length}).",
                    row_index=idx,
                    variant_id=var_id,
                )
            elif seq_len > val_cfg.max_sequence_length:
                report.add_issue(
                    "WARNING",
                    "SEQUENCE",
                    f"Sequence length {seq_len} exceeds typical single-domain range ({val_cfg.max_sequence_length}).",
                    row_index=idx,
                    variant_id=var_id,
                )

            invalid_chars = set(seq_str) - CANONICAL_AMINO_ACIDS
            if invalid_chars:
                report.add_issue(
                    "ERROR",
                    "SEQUENCE",
                    f"Sequence contains non-canonical amino acids or illegal characters: {sorted(invalid_chars)}",
                    row_index=idx,
                    variant_id=var_id,
                )

        # Mutation syntax and consistency validation
        mut_str = row.get("mutations")
        if pd.notna(mut_str):
            try:
                parsed_muts = parse_mutations(str(mut_str))
                if len(parsed_muts) == 0:
                    wt_count += 1
                elif len(parsed_muts) == 1:
                    single_mut_count += 1
                else:
                    multi_mut_count += 1

                # If parent reference sequence provided, check WT residue match
                if (
                    parent_reference_sequences
                    and pd.notna(parent)
                    and str(parent) in parent_reference_sequences
                ):
                    ref_seq = parent_reference_sequences[str(parent)]
                    try:
                        # Attempt to mutate reference sequence and compare
                        reconstructed = apply_mutations_to_sequence(
                            ref_seq, parsed_muts, offset=1, strict_wt_check=True
                        )
                        if pd.notna(seq) and str(seq).strip().upper() != reconstructed:
                            report.add_issue(
                                "WARNING",
                                "MUTATION",
                                "Provided full sequence does not match sequence reconstructed from mutations and reference parent.",
                                row_index=idx,
                                variant_id=var_id,
                            )
                    except (SequenceMismatchError, ValueError) as err:
                        report.add_issue(
                            "ERROR",
                            "MUTATION",
                            f"Mutation inconsistent with reference parent sequence: {err}",
                            row_index=idx,
                            variant_id=var_id,
                        )

            except MutationParseError as e:
                report.add_issue(
                    "ERROR",
                    "MUTATION",
                    f"Invalid mutation string syntax: '{mut_str}' ({e})",
                    row_index=idx,
                    variant_id=var_id,
                )

        # Numeric ranges checks
        # pH
        if "pH" in df.columns and pd.notna(row.get("pH")):
            try:
                ph_val = float(row["pH"])
                if not (val_cfg.ph_min <= ph_val <= val_cfg.ph_max):
                    report.add_issue(
                        "ERROR",
                        "NUMERIC",
                        f"pH value {ph_val} is outside valid physiological/assay bounds [{val_cfg.ph_min}, {val_cfg.ph_max}].",
                        row_index=idx,
                        variant_id=var_id,
                    )
            except (ValueError, TypeError):
                report.add_issue(
                    "ERROR", "NUMERIC", f"Unparseable numeric pH: {row['pH']}", row_index=idx, variant_id=var_id
                )

        # Crystallinity
        if "PET_crystallinity_pct" in df.columns and pd.notna(row.get("PET_crystallinity_pct")):
            try:
                cryst_val = float(row["PET_crystallinity_pct"])
                if not (val_cfg.crystallinity_pct_min <= cryst_val <= val_cfg.crystallinity_pct_max):
                    report.add_issue(
                        "ERROR",
                        "NUMERIC",
                        f"PET crystallinity {cryst_val}% is out of bounds [0, 100].",
                        row_index=idx,
                        variant_id=var_id,
                    )
            except (ValueError, TypeError):
                report.add_issue(
                    "ERROR",
                    "NUMERIC",
                    f"Unparseable numeric PET_crystallinity_pct: {row['PET_crystallinity_pct']}",
                    row_index=idx,
                    variant_id=var_id,
                )

        # Tm
        if "Tm_C" in df.columns and pd.notna(row.get("Tm_C")):
            try:
                tm_val = float(row["Tm_C"])
                if not (val_cfg.tm_celsius_min <= tm_val <= val_cfg.tm_celsius_max):
                    report.add_issue(
                        "ERROR",
                        "NUMERIC",
                        f"Tm value {tm_val} deg C is out of biological bounds [{val_cfg.tm_celsius_min}, {val_cfg.tm_celsius_max}].",
                        row_index=idx,
                        variant_id=var_id,
                    )
            except (ValueError, TypeError):
                report.add_issue(
                    "ERROR", "NUMERIC", f"Unparseable numeric Tm_C: {row['Tm_C']}", row_index=idx, variant_id=var_id
                )

        # Activity
        if "activity_rel_to_parent" in df.columns and pd.notna(row.get("activity_rel_to_parent")):
            try:
                act_val = float(row["activity_rel_to_parent"])
                if act_val < 0.0:
                    report.add_issue(
                        "ERROR",
                        "NUMERIC",
                        f"Negative relative activity {act_val} is physically invalid.",
                        row_index=idx,
                        variant_id=var_id,
                    )
            except (ValueError, TypeError):
                report.add_issue(
                    "ERROR",
                    "NUMERIC",
                    f"Unparseable numeric activity_rel_to_parent: {row['activity_rel_to_parent']}",
                    row_index=idx,
                    variant_id=var_id,
                )

    report.summary_metrics = {
        "total_records": len(df),
        "unique_parents": list(unique_parents),
        "wt_count": wt_count,
        "single_mutant_count": single_mut_count,
        "multi_mutant_count": multi_mut_count,
    }

    return report


def validate_file(
    file_path: Path | str,
    output_report_path: Optional[Path | str] = None,
    config: Optional[QCatalystConfig] = None,
) -> ValidationReport:
    """Validate a parquet or CSV file against canonical QCatalyst specifications.

    Args:
        file_path: Path to dataset file.
        output_report_path: Optional path to save JSON report.
        config: Optional configuration.

    Returns:
        ValidationReport instance.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Target data file not found: {file_path}")

    if file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix in (".csv", ".tsv", ".txt"):
        sep = "\t" if file_path.suffix == ".tsv" else ","
        df = pd.read_csv(file_path, sep=sep)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    report = validate_dataframe(df, config=config)

    if output_report_path:
        report.save_json(output_report_path)

    return report


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "data/curated/variants.parquet"
    print(f"Validating dataset at: {target}")
    try:
        rpt = validate_file(target, output_report_path="data/curated/data_quality_report.json")
        print(f"Validation Result: {'PASSED' if rpt.passed else 'FAILED'}")
        print(f"Errors: {rpt.error_count}, Warnings: {rpt.warning_count}")
        for issue in rpt.issues[:10]:
            print(f" - [{issue.severity}] {issue.category}: {issue.message} (Variant: {issue.variant_id})")
        if len(rpt.issues) > 10:
            print(f" ... and {len(rpt.issues) - 10} more issues.")
        sys.exit(0 if rpt.passed else 1)
    except Exception as e:
        print(f"Validation execution failed: {e}")
        sys.exit(1)
