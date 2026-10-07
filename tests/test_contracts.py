"""Unit tests for pipeline file contracts registry and schema verification."""

import json
from pathlib import Path
import pandas as pd
import pytest
from data.contracts import FILE_CONTRACTS, verify_contract


def test_file_contracts_registry():
    expected_contracts = [
        "phase1_variants",
        "protein_ai",
        "uncertainty",
        "acquisition",
        "chemistry",
        "quantum",
        "fusion",
        "benchmark",
    ]
    for key in expected_contracts:
        assert key in FILE_CONTRACTS
        contract = FILE_CONTRACTS[key]
        assert contract.module_name != ""
        assert contract.relative_path != ""
        assert len(contract.required_columns_or_keys) > 0


def test_verify_contract_missing_file(tmp_path):
    is_valid, issues = verify_contract("phase1_variants", base_dir=tmp_path)
    assert is_valid is False
    assert any("does not exist" in i for i in issues)


def test_verify_contract_valid_parquet(tmp_path):
    contract = FILE_CONTRACTS["protein_ai"]
    target_path = tmp_path / contract.relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Create matching DataFrame
    df = pd.DataFrame({
        "variant_id": ["v1"],
        "prediction": [0.85],
        "zero_shot_score": [-1.2],
        "esm_log_likelihood_ratio": [-0.5],
        "model_version": ["esm2_t33_650M_UR50D"],
    })
    df.to_parquet(target_path)

    is_valid, issues = verify_contract("protein_ai", base_dir=tmp_path)
    assert is_valid is True
    assert len(issues) == 0


def test_verify_contract_missing_column(tmp_path):
    contract = FILE_CONTRACTS["protein_ai"]
    target_path = tmp_path / contract.relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Missing model_version column
    df = pd.DataFrame({
        "variant_id": ["v1"],
        "zero_shot_score": [-1.2],
        "esm_log_likelihood_ratio": [-0.5],
    })
    df.to_parquet(target_path)

    is_valid, issues = verify_contract("protein_ai", base_dir=tmp_path)
    assert is_valid is False
    assert any("model_version" in i for i in issues)
