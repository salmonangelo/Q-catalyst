"""Configuration schema and loader for Q-Catalyst."""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str = "qcatalyst"
    version: str = "0.1.0"
    random_seed: int = 42


class PathsConfig(BaseModel):
    raw_data_dir: Path = Path("data/raw")
    curated_data_dir: Path = Path("data/curated")
    structures_dir: Path = Path("data/structures")
    splits_dir: Path = Path("data/splits")
    logs_dir: Path = Path("logs")
    curated_variants_file: Path = Path("data/curated/variants.parquet")
    quality_report_file: Path = Path("data/curated/data_quality_report.json")


class DatasetConfig(BaseModel):
    primary_benchmark: str = "PET-Gym"
    benchmark_sources: List[str] = Field(default_factory=list)
    required_columns: List[str] = Field(
        default_factory=lambda: ["variant_id", "parent_enzyme", "sequence", "mutations"]
    )


class StructureConfig(BaseModel):
    reference_pdb_id: str = "5XJH"
    reference_pdb_file: Path = Path("data/structures/5xjh.pdb")
    reference_chain_id: str = "A"
    reference_parent: str = "IsPETase"
    catalytic_triad: Dict[str, int] = Field(
        default_factory=lambda: {"Ser": 160, "Asp": 206, "His": 237}
    )
    oxyanion_hole: Dict[str, int] = Field(
        default_factory=lambda: {"Tyr": 87, "Met": 161}
    )
    active_site_radius_angstrom: float = 8.0


class SplittingConfig(BaseModel):
    random_seed: int = 42
    strategies: List[str] = Field(
        default_factory=lambda: [
            "study_grouped",
            "parent_grouped",
            "mutation_complexity",
            "random",
        ]
    )
    default_strategy: str = "study_grouped"
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15


class ValidationConfig(BaseModel):
    strict_amino_acids: bool = True
    allow_non_canonical_aa: bool = False
    min_sequence_length: int = 20
    max_sequence_length: int = 1000
    allowed_activities_min: float = 0.0
    tm_celsius_min: float = 0.0
    tm_celsius_max: float = 120.0
    ph_min: float = 2.0
    ph_max: float = 12.0
    crystallinity_pct_min: float = 0.0
    crystallinity_pct_max: float = 100.0


class DownstreamContractsConfig(BaseModel):
    protein_ai: Path = Path("protein_ai/predictions.parquet")
    uncertainty: Path = Path("uncertainty/uncertainty.parquet")
    acquisition: Path = Path("acquisition/chem_jobs.json")
    chemistry: Path = Path("chemistry/chem_results.parquet")
    quantum: Path = Path("quantum/quantum_results.parquet")
    fusion: Path = Path("fusion/ranking.parquet")
    benchmark: Path = Path("benchmark/benchmark_results.parquet")


class QCatalystConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    structure: StructureConfig = Field(default_factory=StructureConfig)
    splitting: SplittingConfig = Field(default_factory=SplittingConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    downstream_contracts: DownstreamContractsConfig = Field(
        default_factory=DownstreamContractsConfig
    )


def load_config(config_path: Optional[Path | str] = None) -> QCatalystConfig:
    """Load configuration from a YAML file or return defaults.

    Args:
        config_path: Optional path to YAML config. Defaults to 'configs/config.yaml'.

    Returns:
        Validated QCatalystConfig object.
    """
    if config_path is None:
        default_yaml = Path(__file__).parent / "config.yaml"
        if default_yaml.exists():
            config_path = default_yaml
        else:
            return QCatalystConfig()

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return QCatalystConfig.model_validate(data)
