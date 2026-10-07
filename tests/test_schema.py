"""Unit tests for Canonical Schema and VariantRecord validation."""

import pandas as pd
import pytest
from data.schema import CANONICAL_COLUMNS, VariantRecord, enforce_canonical_schema


def test_variant_record_valid():
    rec = VariantRecord(
        variant_id="IsPETase_S160A",
        parent_enzyme="IsPETase",
        sequence="MNPTAASLEASAGPFTVRSFTV",
        mutations="S160A",
        activity_rel_to_parent=1.45,
        pH=7.5,
        PET_crystallinity_pct=15.0,
    )
    assert rec.variant_id == "IsPETase_S160A"
    assert rec.mutations == "S160A"
    assert rec.pH == 7.5
    assert rec.PET_crystallinity_pct == 15.0


def test_variant_record_invalid_sequence():
    with pytest.raises(ValueError, match="non-canonical characters"):
        VariantRecord(
            variant_id="V1",
            parent_enzyme="IsPETase",
            sequence="MNPTAAS123BZ",  # numbers and invalid AA
            mutations="WT",
        )


def test_variant_record_invalid_ph():
    with pytest.raises(ValueError, match="pH must be between 0 and 14"):
        VariantRecord(
            variant_id="V1",
            parent_enzyme="IsPETase",
            sequence="MNPTAASLEASAGPFTVRSFTV",
            pH=16.5,
        )


def test_variant_record_invalid_crystallinity():
    with pytest.raises(ValueError, match="crystallinity % must be between 0 and 100"):
        VariantRecord(
            variant_id="V1",
            parent_enzyme="IsPETase",
            sequence="MNPTAASLEASAGPFTVRSFTV",
            PET_crystallinity_pct=120.0,
        )


def test_enforce_canonical_schema():
    raw_dict = {
        "variant_id": ["V1", "V2"],
        "parent_enzyme": ["IsPETase", "LCC"],
        "sequence": ["MNPTAAS", "MNPTAAS"],
        "custom_unsupported_column": [123, 456],
    }
    df = pd.DataFrame(raw_dict)
    canonical = enforce_canonical_schema(df)

    # Must contain all canonical columns exactly
    assert list(canonical.columns) == CANONICAL_COLUMNS
    # Missing columns should exist and be filled with NaN / None
    assert "activity_rel_to_parent" in canonical.columns
    assert canonical["activity_rel_to_parent"].isna().all()
