"""Unit tests for Phase 5 Quantum Simulation Layer."""

import json
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest

from quantum.active_space import ActiveSpaceData, ActiveSpaceSelector
from quantum.casci import CASCIResult, CASCISolver
from quantum.config import ActiveSpaceConfig, NoiseConfig, QuantumConfig, VQEConfig
from quantum.hamiltonian import HamiltonianBuilder, QubitHamiltonian
from quantum.noise import NoiseSimulator, NoisySimulationResult
from quantum.outputs import (
    QUANTUM_RESULTS_SCHEMA_COLUMNS,
    QuantumOutputWriter,
    VQE_HISTORY_SCHEMA_COLUMNS,
)
from quantum.vqe import VQEResult, VQESolver


@pytest.fixture
def sample_active_space():
    selector = ActiveSpaceSelector()
    return selector.create_synthetic_model_active_space(
        variant_id="TEST_VAR",
        n_electrons=4,
        n_orbitals=4,
        core_energy=-10.0,
        charge=0,
        multiplicity=1,
        seed=42,
    )


@pytest.fixture
def small_active_space():
    selector = ActiveSpaceSelector()
    return selector.create_synthetic_model_active_space(
        variant_id="TEST_SMALL",
        n_electrons=2,
        n_orbitals=2,
        core_energy=-5.0,
        charge=0,
        multiplicity=1,
        seed=42,
    )


def test_active_space_validation(sample_active_space):
    """Verifies physical and dimensional validation of the active space."""
    selector = ActiveSpaceSelector()
    assert sample_active_space.active_electrons == 4
    assert sample_active_space.active_orbitals == 4
    assert sample_active_space.num_spin_orbitals == 8
    assert sample_active_space.h1_integrals.shape == (4, 4)
    assert sample_active_space.h2_integrals.shape == (4, 4, 4, 4)

    # Incompatible electrons vs orbitals should raise ValueError
    with pytest.raises(ValueError, match="exceeds maximum orbital capacity"):
        selector.validate_active_space(
            active_electrons=10,
            active_orbitals=4,
            charge=0,
            multiplicity=1,
            h1=sample_active_space.h1_integrals,
            h2=sample_active_space.h2_integrals,
        )


def test_hamiltonian_jordan_wigner_mapping(sample_active_space):
    """Verifies second-quantized Hamiltonian building and Jordan-Wigner 8-qubit mapping."""
    builder = HamiltonianBuilder(mapping_method="jordan_wigner")
    hamiltonian = builder.build_qubit_hamiltonian(sample_active_space)

    assert hamiltonian.num_qubits == 8
    assert hamiltonian.num_spin_orbitals == 8
    assert hamiltonian.num_pauli_terms > 0
    assert len(hamiltonian.hamiltonian_hash) == 64
    assert hamiltonian.mapping_method == "jordan_wigner"

    # Test serialization to dictionary and JSON
    h_dict = hamiltonian.to_dict()
    assert h_dict["num_qubits"] == 8
    assert len(h_dict["pauli_terms"]) == hamiltonian.num_pauli_terms


def test_casci_exact_diagonalization(sample_active_space):
    """Verifies CASCI exact classical diagonalization."""
    builder = HamiltonianBuilder()
    hamiltonian = builder.build_qubit_hamiltonian(sample_active_space)

    casci_solver = CASCISolver()
    result = casci_solver.compute(hamiltonian, sample_active_space)

    assert result.converged is True
    assert result.num_qubits == 8
    assert result.casci_energy < result.hartree_fock_energy  # Correlation energy must lower total energy
    assert result.correlation_energy < 0.0
    assert result.runtime_seconds >= 0.0


def test_vqe_execution_and_convergence(small_active_space):
    """Verifies VQE simulation and convergence on a small active space."""
    builder = HamiltonianBuilder()
    hamiltonian = builder.build_qubit_hamiltonian(small_active_space)

    casci_solver = CASCISolver()
    casci_res = casci_solver.compute(hamiltonian, small_active_space)

    vqe_config = VQEConfig(
        ansatz_type="TwoLocal",
        ansatz_reps=2,
        optimizer_type="COBYLA",
        optimizer_maxiter=50,
        random_seed=42,
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        vqe_solver = VQESolver(config=vqe_config, cache_dir=tmp_dir)
        vqe_res = vqe_solver.compute(hamiltonian, small_active_space, casci_result=casci_res)

        assert vqe_res.num_qubits == 4
        assert vqe_res.converged is True
        assert vqe_res.vqe_energy is not None
        assert vqe_res.vqe_absolute_error is not None
        assert len(vqe_res.history) > 0

        # Verification of cache file
        cache_files = list(Path(tmp_dir).glob("vqe_*.json"))
        assert len(cache_files) == 1


def test_noise_simulation(small_active_space):
    """Verifies optional depolarizing noise simulation."""
    builder = HamiltonianBuilder()
    hamiltonian = builder.build_qubit_hamiltonian(small_active_space)

    casci_solver = CASCISolver()
    casci_res = casci_solver.compute(hamiltonian, small_active_space)

    vqe_solver = VQESolver()
    vqe_res = vqe_solver.compute(hamiltonian, small_active_space, casci_result=casci_res)

    noise_config = NoiseConfig(
        enabled=True,
        noise_model_type="depolarizing",
        depolarizing_1q_rate=0.001,
        depolarizing_2q_rate=0.01,
    )
    simulator = NoiseSimulator(config=noise_config)
    noisy_res = simulator.evaluate_noisy_vqe(
        vqe_solver=vqe_solver,
        hamiltonian=hamiltonian,
        noiseless_result=vqe_res,
        casci_result=casci_res,
    )

    assert noisy_res.noise_enabled is True
    assert noisy_res.noisy_vqe_energy is not None
    assert noisy_res.noisy_absolute_error is not None


def test_quantum_output_serialization(small_active_space):
    """Verifies parquet export and manifest generation for quantum simulation."""
    builder = HamiltonianBuilder()
    hamiltonian = builder.build_qubit_hamiltonian(small_active_space)

    casci_solver = CASCISolver()
    casci_res = casci_solver.compute(hamiltonian, small_active_space)

    vqe_solver = VQESolver()
    vqe_res = vqe_solver.compute(hamiltonian, small_active_space, casci_result=casci_res)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        results_parquet = tmp_path / "quantum_results.parquet"
        history_parquet = tmp_path / "vqe_history.parquet"
        manifest_json = tmp_path / "quantum_manifest.json"

        writer = QuantumOutputWriter(output_dir=tmp_path)
        df_results = writer.build_quantum_results_dataframe(
            vqe_result=vqe_res,
            casci_result=casci_res,
            hamiltonian=hamiltonian,
            data_source="synthetic_test_fixture",
            data_quality_flag="SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA",
        )
        for col in QUANTUM_RESULTS_SCHEMA_COLUMNS:
            assert col in df_results.columns

        writer.save_results_parquet(df_results, results_parquet)
        assert results_parquet.exists()

        df_history = writer.build_vqe_history_dataframe(vqe_res)
        for col in VQE_HISTORY_SCHEMA_COLUMNS:
            assert col in df_history.columns

        writer.save_history_parquet(df_history, history_parquet)
        assert history_parquet.exists()

        writer.save_quantum_manifest(
            vqe_result=vqe_res,
            casci_result=casci_res,
            hamiltonian=hamiltonian,
            active_space=small_active_space,
            output_path=manifest_json,
        )
        assert manifest_json.exists()
