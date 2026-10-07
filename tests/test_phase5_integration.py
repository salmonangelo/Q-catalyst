"""Integration tests for Phase 5 Quantum Simulation Layer."""

from pathlib import Path
import tempfile
import pandas as pd
import pytest

from data.contracts import verify_contract
from quantum.config import ActiveSpaceConfig, NoiseConfig, QuantumConfig, VQEConfig
from quantum.evaluate import QuantumPipeline


def test_phase5_end_to_end_pipeline():
    """Verifies complete Phase 5 end-to-end flow from candidates to quantum_results.parquet."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        chem_results_path = tmp_path / "chem_results.parquet"
        quantum_results_path = tmp_path / "quantum_results.parquet"
        vqe_history_path = tmp_path / "vqe_history.parquet"
        quantum_manifest_path = tmp_path / "quantum_manifest.json"
        active_space_manifest_path = tmp_path / "active_space_manifest.json"
        hamiltonians_dir = tmp_path / "hamiltonians"
        cache_dir = tmp_path / "cache"

        # Create mock chemistry results input
        chem_data = [
            {
                "variant_id": "VAR_WT",
                "parent_enzyme": "IsPETase",
                "mutations": "WT",
                "pdb_id": "5XJH",
                "chain_id": "A",
                "cluster_id": "WT_5XJH_active_site",
                "cluster_atom_count": 60,
                "cluster_residue_count": 7,
                "geometry_source": "experimental_structure",
                "geometry_status": "valid",
                "charge": 0,
                "multiplicity": 1,
                "method": "HF",
                "basis": "sto-3g",
                "scf_converged": True,
                "scf_iterations": 10,
                "total_energy": -150.25,
                "runtime_seconds": 0.5,
                "dipole_x": 0.1,
                "dipole_y": 0.2,
                "dipole_z": 0.3,
                "dipole_magnitude": 0.374,
                "homo_energy": -0.35,
                "lumo_energy": 0.05,
                "homo_lumo_gap": 0.40,
                "reference_energy": -150.25,
                "delta_energy": 0.0,
                "calculation_status": "COMPLETED",
                "failure_reason": None,
                "data_source": "synthetic_test_fixture",
                "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA",
            }
        ]
        pd.DataFrame(chem_data).to_parquet(chem_results_path, index=False)

        # Configure pipeline
        config = QuantumConfig(
            active_space=ActiveSpaceConfig(active_electrons=4, active_orbitals=4),
            vqe=VQEConfig(
                ansatz_type="TwoLocal",
                ansatz_reps=2,
                optimizer_type="COBYLA",
                optimizer_maxiter=50,
                random_seed=42,
            ),
            noise=NoiseConfig(enabled=True, noise_model_type="depolarizing"),
            cache_dir=cache_dir,
            hamiltonians_dir=hamiltonians_dir,
            output_results_parquet=quantum_results_path,
            output_vqe_history_parquet=vqe_history_path,
            output_quantum_manifest=quantum_manifest_path,
            output_active_space_manifest=active_space_manifest_path,
        )

        pipeline = QuantumPipeline(config=config, test_fixture_mode=True)
        df_results = pipeline.run(
            chem_results_path=chem_results_path,
            variant_id="VAR_WT",
            enable_noise=True,
        )

        # 1. Output file existence checks
        assert quantum_results_path.exists()
        assert vqe_history_path.exists()
        assert quantum_manifest_path.exists()
        assert active_space_manifest_path.exists()

        # 2. Results DataFrame checks
        assert len(df_results) == 1
        row = df_results.iloc[0]
        assert row["variant_id"] == "VAR_WT"
        assert row["active_electrons"] == 4
        assert row["active_orbitals"] == 4
        assert row["initial_qubits"] == 8
        assert row["mapping_method"] == "jordan_wigner"
        assert row["casci_energy"] is not None
        assert row["vqe_energy"] is not None
        assert row["vqe_absolute_error"] is not None
        assert bool(row["noise_enabled"]) is True
        assert row["noisy_vqe_energy"] is not None
        assert row["calculation_status"] == "COMPLETED"
        assert row["data_quality_flag"] == "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"

        # 3. History DataFrame checks
        df_hist = pd.read_parquet(vqe_history_path)
        assert len(df_hist) > 0
        assert "energy" in df_hist.columns
        assert "energy_error_vs_casci" in df_hist.columns
