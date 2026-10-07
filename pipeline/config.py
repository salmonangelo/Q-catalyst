"""Configuration schemas for Phase 7 Pipeline Orchestration."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuantumPolicyConfig(BaseModel):
    """Execution policy for active-space quantum simulation."""
    quantum_mode: str = "representative"  # 'representative' or 'all'
    representative_selection: str = "top_ranked"  # 'top_ranked', 'wildtype', or 'first'
    max_quantum_candidates: int = 1
    enable_noise: bool = False


class PipelineConfig(BaseModel):
    """Master configuration for end-to-end hybrid quantum-classical pipeline execution."""
    pipeline_name: str = "qcatalyst_end_to_end"
    version: str = "0.1.0"
    random_seed: int = 42
    
    # Run directory root
    output_root: Path = Path("runs")
    
    # Stage enablement
    enabled_stages: List[str] = Field(
        default_factory=lambda: [
            "data",
            "protein_ai",
            "uncertainty",
            "acquisition",
            "chemistry",
            "quantum",
            "fusion",
        ]
    )
    
    # Stage error policies
    fail_fast: bool = True
    optional_stages: List[str] = Field(default_factory=lambda: ["quantum"])
    reuse_cached_outputs: bool = True
    
    # Candidate batch control
    candidate_limit: Optional[int] = None
    candidate_selection_policy: str = "deterministic_top"
    
    # Quantum simulation policy
    quantum_policy: QuantumPolicyConfig = Field(default_factory=QuantumPolicyConfig)
    
    # Policies
    synthetic_data_policy: str = "preserve_provenance"
    split_strategy: str = "mutation_complexity"
    
    # Input/Output Contract paths (defaults)
    variants_parquet: Path = Path("data/curated/variants.parquet")
    protein_ai_parquet: Path = Path("protein_ai/predictions.parquet")
    uncertainty_parquet: Path = Path("uncertainty/uncertainty.parquet")
    gate0_report_json: Path = Path("uncertainty/gate0_report.json")
    acquisition_parquet: Path = Path("acquisition/selected_candidates.parquet")
    chem_jobs_json: Path = Path("acquisition/chem_jobs.json")
    chemistry_parquet: Path = Path("chemistry/chem_results.parquet")
    cluster_manifest_json: Path = Path("chemistry/clusters/cluster_manifest.json")
    quantum_parquet: Path = Path("quantum/quantum_results.parquet")
    quantum_manifest_json: Path = Path("quantum/quantum_manifest.json")
    fusion_results_parquet: Path = Path("fusion/fusion_results.parquet")
    evidence_matrix_parquet: Path = Path("fusion/evidence_matrix.parquet")
    fusion_manifest_json: Path = Path("fusion/fusion_manifest.json")
    candidate_explanations_json: Path = Path("fusion/candidate_explanations.json")
