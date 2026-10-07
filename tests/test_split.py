"""Unit tests for dataset splitting strategies and reproducibility."""

import pandas as pd
import pytest
from data.split import DatasetSplitter, SplitManifest


@pytest.fixture
def mock_dataset():
    records = []
    studies = ["Study_1", "Study_2", "Study_3", "Study_4", "Study_5"]
    parents = ["IsPETase", "LCC", "TfCut2", "PE-H"]

    for i in range(50):
        study = studies[i % len(studies)]
        parent = parents[i % len(parents)]
        is_multi = (i % 3 == 0)
        muts = "S160A;D206G" if is_multi else ("WT" if i == 0 else f"S{100+i}A")
        records.append({
            "variant_id": f"var_{i:03d}",
            "parent_enzyme": parent,
            "sequence": "QTNPYARGPNPTAASLEASAGPFTVRSFTVSRPSGYGAGTVYYPTNAGGTVGAIAIVPGYTARQSSIKWWGPR",
            "mutations": muts,
            "activity_rel_to_parent": 1.0 + (i * 0.05),
            "study_id": study,
        })
    return pd.DataFrame(records)


def test_split_study_grouped_no_leakage(mock_dataset):
    splitter = DatasetSplitter()
    manifest = splitter.split(mock_dataset, strategy="study_grouped", random_seed=42)

    assert isinstance(manifest, SplitManifest)
    assert manifest.train_count > 0
    assert manifest.val_count > 0
    assert manifest.test_count > 0

    # Ensure zero overlap in variant IDs
    train_set = set(manifest.train_variant_ids)
    val_set = set(manifest.val_variant_ids)
    test_set = set(manifest.test_variant_ids)
    assert train_set.isdisjoint(val_set)
    assert train_set.isdisjoint(test_set)
    assert val_set.isdisjoint(test_set)

    # Ensure zero overlap in study groups
    train_studies = set(mock_dataset[mock_dataset["variant_id"].isin(train_set)]["study_id"])
    val_studies = set(mock_dataset[mock_dataset["variant_id"].isin(val_set)]["study_id"])
    test_studies = set(mock_dataset[mock_dataset["variant_id"].isin(test_set)]["study_id"])
    assert train_studies.isdisjoint(val_studies)
    assert train_studies.isdisjoint(test_studies)
    assert val_studies.isdisjoint(test_studies)


def test_split_parent_grouped_no_leakage(mock_dataset):
    splitter = DatasetSplitter()
    manifest = splitter.split(mock_dataset, strategy="parent_grouped", random_seed=42)

    train_parents = set(mock_dataset[mock_dataset["variant_id"].isin(manifest.train_variant_ids)]["parent_enzyme"])
    val_parents = set(mock_dataset[mock_dataset["variant_id"].isin(manifest.val_variant_ids)]["parent_enzyme"])
    test_parents = set(mock_dataset[mock_dataset["variant_id"].isin(manifest.test_variant_ids)]["parent_enzyme"])

    assert train_parents.isdisjoint(val_parents)
    assert train_parents.isdisjoint(test_parents)
    assert val_parents.isdisjoint(test_parents)


def test_split_mutation_complexity(mock_dataset):
    splitter = DatasetSplitter()
    manifest = splitter.split(mock_dataset, strategy="mutation_complexity", random_seed=42)

    train_muts = mock_dataset[mock_dataset["variant_id"].isin(manifest.train_variant_ids)]["mutations"]
    val_muts = mock_dataset[mock_dataset["variant_id"].isin(manifest.val_variant_ids)]["mutations"]

    # All train mutations must be single or WT
    for m in train_muts:
        assert ";" not in m

    # All val/test mutations must be multi-site
    for m in val_muts:
        assert ";" in m


def test_split_reproducibility(mock_dataset):
    splitter = DatasetSplitter()
    m1 = splitter.split(mock_dataset, strategy="study_grouped", random_seed=123)
    m2 = splitter.split(mock_dataset, strategy="study_grouped", random_seed=123)
    assert m1.train_variant_ids == m2.train_variant_ids
    assert m1.val_variant_ids == m2.val_variant_ids
    assert m1.test_variant_ids == m2.test_variant_ids
