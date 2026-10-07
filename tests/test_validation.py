"""Unit tests for dataset validation rules and anomaly reporting."""

import json
from pathlib import Path
import pandas as pd
import pytest
from data.schema import enforce_canonical_schema
from data.validate import validate_dataframe


@pytest.fixture
def valid_dataframe():
    df = pd.DataFrame([
        {
            "variant_id": "IsPETase_WT",
            "parent_enzyme": "IsPETase",
            "sequence": "QTNPYARGPNPTAASLEASAGPFTVRSFTVSRPSGYGAGTVYYPTNAGGTVGAIAIVPGYTARQSSIKWWGPR",
            "mutations": "WT",
            "activity_rel_to_parent": 1.0,
            "pH": 7.0,
            "PET_crystallinity_pct": 10.0,
            "Tm_C": 50.5,
            "study_id": "Study_A",
        },
        {
            "variant_id": "IsPETase_S160A",
            "parent_enzyme": "IsPETase",
            "sequence": "QTNPYARGPNPTAASLEASAGPFTVRSFTVSRPSGYGAGTVYYPTNAGGTVGAIAIVPGYTARQSSIKWWGPR",
            "mutations": "S160A",
            "activity_rel_to_parent": 0.05,
            "pH": 7.0,
            "PET_crystallinity_pct": 10.0,
            "Tm_C": 48.0,
            "study_id": "Study_A",
        },
    ])
    return enforce_canonical_schema(df)


def test_validate_valid_dataframe(valid_dataframe):
    report = validate_dataframe(valid_dataframe)
    assert report.passed is True
    assert report.error_count == 0
    assert report.total_records == 2


def test_validate_empty_dataframe():
    empty_df = pd.DataFrame()
    report = validate_dataframe(empty_df)
    assert report.passed is False
    assert report.error_count > 0
    assert any(i.category == "EMPTY" for i in report.issues)


def test_validate_duplicate_variant_id(valid_dataframe):
    dup_df = pd.concat([valid_dataframe, valid_dataframe.iloc[[0]]], ignore_index=True)
    report = validate_dataframe(dup_df)
    assert report.passed is False
    assert any(i.category == "DUPLICATE" for i in report.issues)


def test_validate_non_canonical_amino_acid(valid_dataframe):
    corrupt_df = valid_dataframe.copy()
    corrupt_df.loc[0, "sequence"] = "QTNPYARGPNPTAA123"  # illegal characters
    report = validate_dataframe(corrupt_df)
    assert report.passed is False
    assert any(i.category == "SEQUENCE" for i in report.issues)


def test_validate_invalid_numeric_values(valid_dataframe):
    invalid_df = valid_dataframe.copy()
    invalid_df.loc[0, "pH"] = 18.0  # impossible pH
    invalid_df.loc[1, "activity_rel_to_parent"] = -2.5  # negative activity
    report = validate_dataframe(invalid_df)
    assert report.passed is False
    numeric_issues = [i for i in report.issues if i.category == "NUMERIC"]
    assert len(numeric_issues) >= 2


def test_validate_report_json_export(valid_dataframe, tmp_path):
    report = validate_dataframe(valid_dataframe)
    out_file = tmp_path / "report.json"
    report.save_json(out_file)
    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["passed"] is True
    assert data["total_records"] == 2
