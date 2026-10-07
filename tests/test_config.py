"""Unit tests for configuration loading and validation."""

from pathlib import Path
from configs.config_schema import QCatalystConfig, load_config


def test_load_default_config():
    cfg = load_config()
    assert isinstance(cfg, QCatalystConfig)
    assert cfg.project.name == "qcatalyst"
    assert cfg.structure.reference_pdb_id == "5XJH"
    assert cfg.structure.catalytic_triad["Ser"] == 160
    assert cfg.structure.catalytic_triad["Asp"] == 206
    assert cfg.structure.catalytic_triad["His"] == 237


def test_config_paths():
    cfg = load_config()
    assert cfg.paths.raw_data_dir == Path("data/raw")
    assert cfg.paths.curated_data_dir == Path("data/curated")
    assert cfg.paths.structures_dir == Path("data/structures")
    assert cfg.paths.splits_dir == Path("data/splits")
