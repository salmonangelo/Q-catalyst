"""Output serialization for Phase 5 quantum results, VQE history, and manifests."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from quantum.active_space import ActiveSpaceData
from quantum.casci import CASCIResult
from quantum.hamiltonian import QubitHamiltonian
from quantum.noise import NoisySimulationResult
from quantum.vqe import VQEResult


QUANTUM_RESULTS_SCHEMA_COLUMNS = [
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
    "ansatz",
    "ansatz_depth",
    "initial_energy",
    "final_energy",
    "noise_enabled",
    "noise_model",
    "noisy_vqe_energy",
    "noisy_absolute_error",
    "runtime_seconds",
    "backend",
    "calculation_status",
    "failure_reason",
    "data_source",
    "data_quality_flag",
]

VQE_HISTORY_SCHEMA_COLUMNS = [
    "variant_id",
    "iteration",
    "energy",
    "energy_error_vs_casci",
    "noise_enabled",
]


class QuantumOutputWriter:
    """Handles serialization of quantum parquet tables, manifests, and Hamiltonians."""

    def __init__(self, output_dir: Path | str = "quantum"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_quantum_results_dataframe(
        self,
        vqe_result: VQEResult,
        casci_result: CASCIResult,
        hamiltonian: QubitHamiltonian,
        noisy_result: Optional[NoisySimulationResult] = None,
        data_source: str = "IsPETase_5XJH_Reduced_Cluster",
        data_quality_flag: str = "SIMULATED_QUANTUM_VQE_EXPERIMENT",
    ) -> pd.DataFrame:
        """Constructs a strictly typed pandas DataFrame conforming to quantum results contract."""
        noise_on = noisy_result.noise_enabled if noisy_result else False
        noise_m = noisy_result.noise_model if noisy_result else "none"
        noisy_e = noisy_result.noisy_vqe_energy if noisy_result else None
        noisy_err = noisy_result.noisy_absolute_error if noisy_result else None

        row = {
            "variant_id": str(vqe_result.variant_id),
            "active_electrons": int(vqe_result.active_electrons),
            "active_orbitals": int(vqe_result.active_orbitals),
            "initial_qubits": int(hamiltonian.num_qubits),
            "final_qubits": int(hamiltonian.num_qubits),
            "mapping_method": str(hamiltonian.mapping_method),
            "casci_energy": float(casci_result.casci_energy),
            "vqe_energy": float(vqe_result.vqe_energy),
            "vqe_absolute_error": float(vqe_result.vqe_absolute_error) if vqe_result.vqe_absolute_error is not None else None,
            "optimizer": str(vqe_result.optimizer),
            "iterations": int(vqe_result.iterations),
            "ansatz": str(vqe_result.ansatz),
            "ansatz_depth": int(vqe_result.ansatz_depth),
            "initial_energy": float(vqe_result.initial_energy),
            "final_energy": float(vqe_result.final_energy),
            "noise_enabled": bool(noise_on),
            "noise_model": str(noise_m),
            "noisy_vqe_energy": float(noisy_e) if noisy_e is not None else None,
            "noisy_absolute_error": float(noisy_err) if noisy_err is not None else None,
            "runtime_seconds": float(vqe_result.runtime_seconds + casci_result.runtime_seconds),
            "backend": str(vqe_result.backend),
            "calculation_status": "COMPLETED" if vqe_result.converged else "CONVERGENCE_FAILED",
            "failure_reason": str(vqe_result.failure_reason) if vqe_result.failure_reason else None,
            "data_source": str(data_source),
            "data_quality_flag": str(data_quality_flag),
        }

        df = pd.DataFrame([row])
        for col in QUANTUM_RESULTS_SCHEMA_COLUMNS:
            if col not in df.columns:
                df[col] = None

        return df[QUANTUM_RESULTS_SCHEMA_COLUMNS]

    def build_vqe_history_dataframe(
        self,
        vqe_result: VQEResult,
    ) -> pd.DataFrame:
        """Constructs pandas DataFrame for VQE energy optimization history."""
        rows = []
        for entry in vqe_result.history:
            rows.append({
                "variant_id": str(vqe_result.variant_id),
                "iteration": int(entry["iteration"]),
                "energy": float(entry["energy"]),
                "energy_error_vs_casci": float(entry["energy_error_vs_casci"]) if entry["energy_error_vs_casci"] is not None else None,
                "noise_enabled": bool(entry.get("noise_enabled", False)),
            })

        df = pd.DataFrame(rows)
        for col in VQE_HISTORY_SCHEMA_COLUMNS:
            if col not in df.columns:
                df[col] = None

        return df[VQE_HISTORY_SCHEMA_COLUMNS]

    def save_results_parquet(
        self,
        df: pd.DataFrame,
        output_path: Path | str = "quantum/quantum_results.parquet",
    ) -> Path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(p, index=False)
        return p

    def save_history_parquet(
        self,
        df: pd.DataFrame,
        output_path: Path | str = "quantum/vqe_history.parquet",
    ) -> Path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(p, index=False)
        return p

    def save_quantum_manifest(
        self,
        vqe_result: VQEResult,
        casci_result: CASCIResult,
        hamiltonian: QubitHamiltonian,
        active_space: ActiveSpaceData,
        noisy_result: Optional[NoisySimulationResult] = None,
        output_path: Path | str = "quantum/quantum_manifest.json",
    ) -> Path:
        """Writes machine-readable manifest summarizing the complete quantum experiment."""
        manifest_data = {
            "version": "1.0.0",
            "experiment_type": "Classical_Simulation_of_VQE",
            "variant_id": vqe_result.variant_id,
            "active_space": {
                "electrons": active_space.active_electrons,
                "orbitals": active_space.active_orbitals,
                "spin_orbitals": active_space.num_spin_orbitals,
                "orbital_indices": active_space.orbital_indices,
                "selection_method": active_space.selection_method,
            },
            "qubit_hamiltonian": {
                "num_qubits": hamiltonian.num_qubits,
                "num_pauli_terms": hamiltonian.num_pauli_terms,
                "hamiltonian_hash": hamiltonian.hamiltonian_hash,
                "mapping": hamiltonian.mapping_method,
            },
            "casci_reference": {
                "energy": casci_result.casci_energy,
                "hartree_fock_energy": casci_result.hartree_fock_energy,
                "correlation_energy": casci_result.correlation_energy,
                "converged": casci_result.converged,
                "backend": casci_result.backend,
            },
            "vqe_results": {
                "energy": vqe_result.vqe_energy,
                "absolute_error_vs_casci": vqe_result.vqe_absolute_error,
                "validation_tier": vqe_result.validation_tier,
                "optimizer": vqe_result.optimizer,
                "iterations": vqe_result.iterations,
                "ansatz": vqe_result.ansatz,
                "ansatz_depth": vqe_result.ansatz_depth,
                "backend": vqe_result.backend,
                "converged": vqe_result.converged,
            },
            "noise_simulation": {
                "enabled": noisy_result.noise_enabled if noisy_result else False,
                "model": noisy_result.noise_model if noisy_result else "none",
                "noisy_energy": noisy_result.noisy_vqe_energy if noisy_result else None,
                "noisy_error_vs_casci": noisy_result.noisy_absolute_error if noisy_result else None,
            },
        }

        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        return p

    def save_active_space_manifest(
        self,
        active_space: ActiveSpaceData,
        output_path: Path | str = "quantum/active_space_manifest.json",
    ) -> Path:
        """Writes active-space manifest JSON."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(active_space.to_manifest_dict(), f, indent=2)
        return p
