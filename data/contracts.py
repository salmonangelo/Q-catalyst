"""Formal file contracts and schemas for downstream Q-Catalyst pipeline phases."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class FileContract:
    """Specification of an inter-module file contract."""
    module_name: str
    relative_path: str
    file_type: str  # 'parquet', 'json', 'yaml'
    required_columns_or_keys: List[str]
    description: str


# System-wide file contract registry
FILE_CONTRACTS: Dict[str, FileContract] = {
    "phase1_variants": FileContract(
        module_name="data",
        relative_path="data/curated/variants.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "variant_id",
            "parent_enzyme",
            "sequence",
            "mutations",
            "activity_rel_to_parent",
            "data_quality_flag",
        ],
        description="Curated, validated variant dataset with canonical sequences, mutations, and activities.",
    ),
    "protein_ai": FileContract(
        module_name="protein_ai",
        relative_path="protein_ai/predictions.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "variant_id",
            "prediction",
            "zero_shot_score",
            "esm_log_likelihood_ratio",
            "model_version",
        ],
        description="Phase 2 protein language model sequence fitness predictions and embeddings.",
    ),
    "uncertainty": FileContract(
        module_name="uncertainty",
        relative_path="uncertainty/uncertainty.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "variant_id",
            "prediction",
            "ensemble_std",
            "ood_score",
            "conformal_lower",
            "conformal_upper",
            "uncertainty_score",
        ],
        description="Phase 2 calibrated uncertainty and OOD estimates for variant predictions.",
    ),
    "acquisition": FileContract(
        module_name="acquisition",
        relative_path="acquisition/chem_jobs.json",
        file_type="json",
        required_columns_or_keys=[
            "job_id",
            "variant_id",
            "mutations",
            "active_site_residues",
            "qm_method_requested",
            "selection_rank",
        ],
        description="Phase 3 active learning triage queue specifying high-value variants for QM simulation.",
    ),
    "acquisition_candidates": FileContract(
        module_name="acquisition",
        relative_path="acquisition/selected_candidates.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "job_id",
            "variant_id",
            "mutations",
            "predicted_performance",
            "acquisition_score",
            "selection_rank",
            "selection_reason",
        ],
        description="Phase 3 tabular candidate list for downstream chemistry modeling.",
    ),
    "chemistry": FileContract(
        module_name="chemistry",
        relative_path="chemistry/chem_results.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "variant_id",
            "cluster_id",
            "geometry_source",
            "geometry_status",
            "method",
            "basis",
            "scf_converged",
            "total_energy",
            "delta_energy",
            "calculation_status",
        ],
        description="Phase 4 classical electronic structure results and mechanistic descriptors.",
    ),
    "cluster_manifest": FileContract(
        module_name="chemistry",
        relative_path="chemistry/clusters/cluster_manifest.json",
        file_type="json",
        required_columns_or_keys=[
            "version",
            "cluster_count",
            "clusters",
        ],
        description="Phase 4 machine-readable manifest of active-site clusters for downstream quantum simulations.",
    ),
    "quantum": FileContract(
        module_name="quantum",
        relative_path="quantum/quantum_results.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "variant_id",
            "active_electrons",
            "active_orbitals",
            "initial_qubits",
            "final_qubits",
            "mapping_method",
            "casci_energy",
            "vqe_energy",
            "vqe_absolute_error",
            "optimizer",
            "iterations",
            "calculation_status",
        ],
        description="Phase 5 active-space quantum chemical simulation and VQE energy convergence results.",
    ),
    "vqe_history": FileContract(
        module_name="quantum",
        relative_path="quantum/vqe_history.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "variant_id",
            "iteration",
            "energy",
            "energy_error_vs_casci",
        ],
        description="Phase 5 iteration-by-iteration VQE energy optimization trajectory.",
    ),
    "quantum_manifest": FileContract(
        module_name="quantum",
        relative_path="quantum/quantum_manifest.json",
        file_type="json",
        required_columns_or_keys=[
            "version",
            "variant_id",
            "active_space",
            "qubit_hamiltonian",
            "casci_reference",
            "vqe_results",
        ],
        description="Phase 5 machine-readable manifest summarizing quantum simulation and VQE validation.",
    ),
    "active_space_manifest": FileContract(
        module_name="quantum",
        relative_path="quantum/active_space_manifest.json",
        file_type="json",
        required_columns_or_keys=[
            "variant_id",
            "active_electrons",
            "active_orbitals",
            "num_spin_orbitals",
            "orbital_indices",
        ],
        description="Phase 5 active space orbital definitions and integral properties.",
    ),
    "fusion": FileContract(
        module_name="fusion",
        relative_path="fusion/fusion_results.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "candidate_id",
            "rank",
            "fusion_score",
            "decision_status",
            "confidence_label",
            "evidence_coverage_score",
            "protein_ai_score",
            "uncertainty_quality_score",
            "mechanism_proximity_score",
            "chemistry_score",
            "quantum_score",
            "diversity_score",
        ],
        description="Phase 6 multimodal triage ranking combining sequence AI, uncertainty, mechanism, chemistry, quantum, and diversity.",
    ),
    "fusion_results": FileContract(
        module_name="fusion",
        relative_path="fusion/fusion_results.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "candidate_id",
            "rank",
            "fusion_score",
            "decision_status",
            "confidence_label",
            "evidence_coverage_score",
            "protein_ai_score",
            "uncertainty_quality_score",
            "mechanism_proximity_score",
            "chemistry_score",
            "quantum_score",
            "diversity_score",
        ],
        description="Phase 6 primary candidate triage ranking table.",
    ),
    "evidence_matrix": FileContract(
        module_name="fusion",
        relative_path="fusion/evidence_matrix.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "candidate_id",
            "evidence_name",
            "raw_value",
            "normalized_value",
            "normalization_method",
            "source_module",
            "source_artifact",
            "data_quality_flag",
            "available",
            "synthetic",
        ],
        description="Phase 6 granular evidence matrix tracing provenance across all multimodal channels.",
    ),
    "fusion_manifest": FileContract(
        module_name="fusion",
        relative_path="fusion/fusion_manifest.json",
        file_type="json",
        required_columns_or_keys=[
            "timestamp",
            "phase",
            "candidate_count",
            "weights_configured",
            "policies",
            "triage_summary",
            "provenance_and_backends",
        ],
        description="Phase 6 execution manifest with run metadata, status distribution, and guardrails.",
    ),
    "candidate_explanations": FileContract(
        module_name="fusion",
        relative_path="fusion/candidate_explanations.json",
        file_type="json",
        required_columns_or_keys=[
            "candidates",
            "by_id",
        ],
        description="Phase 6 structured, deterministic candidate explanations and factor breakdowns.",
    ),
    "benchmark": FileContract(
        module_name="benchmark",
        relative_path="benchmark/benchmark_results.parquet",
        file_type="parquet",
        required_columns_or_keys=[
            "split_strategy",
            "metric_name",
            "metric_value",
            "baseline_comparison",
        ],
        description="Phase 8 validation metrics against PET-Gym and literature benchmarks.",
    ),
}


def verify_contract(contract_key: str, base_dir: Path | str = ".") -> Tuple[bool, List[str]]:
    """Verify whether a module output file satisfies its registered contract.

    Args:
        contract_key: Key in FILE_CONTRACTS (e.g. 'phase1_variants', 'protein_ai').
        base_dir: Project root directory.

    Returns:
        Tuple of (is_valid: bool, issues: List[str]).
    """
    if contract_key not in FILE_CONTRACTS:
        raise KeyError(f"Unknown contract key '{contract_key}'. Available: {list(FILE_CONTRACTS.keys())}")

    contract = FILE_CONTRACTS[contract_key]
    file_path = Path(base_dir) / contract.relative_path

    issues: List[str] = []

    if not file_path.exists():
        return False, [f"Target file does not exist: {file_path}"]

    try:
        if contract.file_type == "parquet":
            df = pd.read_parquet(file_path)
            missing = [c for c in contract.required_columns_or_keys if c not in df.columns]
            if missing:
                issues.append(f"Missing required columns in {file_path}: {missing}")
        elif contract.file_type == "json":
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    missing = [k for k in contract.required_columns_or_keys if k not in data[0]]
                    if missing:
                        issues.append(f"JSON items missing required keys: {missing}")
                elif len(data) == 0:
                    issues.append("JSON list is empty.")
            elif isinstance(data, dict):
                if "candidates" in data and isinstance(data["candidates"], list):
                    if len(data["candidates"]) > 0:
                        missing = [k for k in contract.required_columns_or_keys if k not in data["candidates"][0]]
                        if missing:
                            issues.append(f"JSON candidate items missing required keys: {missing}")
                    else:
                        issues.append("JSON candidates list is empty.")
                else:
                    missing = [k for k in contract.required_columns_or_keys if k not in data]
                    if missing:
                        issues.append(f"JSON object missing required keys: {missing}")
    except Exception as e:
        issues.append(f"Failed to read file {file_path}: {e}")

    return (len(issues) == 0, issues)
