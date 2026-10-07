"""Configuration schemas for Phase 5 Quantum Simulation Layer."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActiveSpaceConfig(BaseModel):
    """Configuration for active-space selection (electrons, orbitals, and selection strategy)."""
    active_electrons: int = 4  # (4e, 4o) target active space
    active_orbitals: int = 4   # 4 spatial orbitals -> 8 spin-orbitals / qubits
    selection_strategy: str = "frontier_homo_lumo"  # Options: 'frontier_homo_lumo', 'manual_indices'
    manual_orbital_indices: Optional[List[int]] = None
    charge: int = 0
    spin_multiplicity: int = 1


class VQEConfig(BaseModel):
    """Configuration for Variational Quantum Eigensolver (ansatz, optimizer, initial state)."""
    ansatz_type: str = "TwoLocal"  # Options: 'TwoLocal', 'EfficientSU2', 'RealAmplitudes'
    ansatz_reps: int = 2
    ansatz_entanglement: str = "linear"  # Options: 'linear', 'full', 'circular'
    ansatz_rotation_blocks: List[str] = Field(default_factory=lambda: ["ry"])
    ansatz_entanglement_blocks: List[str] = Field(default_factory=lambda: ["cz"])
    initial_state_type: str = "HartreeFock"  # Options: 'HartreeFock', 'Zero'
    optimizer_type: str = "COBYLA"  # Options: 'COBYLA', 'SPSA', 'L-BFGS-B'
    optimizer_maxiter: int = 100
    optimizer_tol: float = 1e-6
    random_seed: int = 42


class NoiseConfig(BaseModel):
    """Configuration for optional simulated quantum noise modeling."""
    enabled: bool = False
    noise_model_type: str = "depolarizing"  # Options: 'depolarizing', 'readout_error'
    depolarizing_1q_rate: float = 0.001
    depolarizing_2q_rate: float = 0.01
    readout_error_rate: float = 0.02
    shots: int = 1024


class QuantumConfig(BaseModel):
    """Unified configuration for Phase 5 Quantum Simulation."""
    active_space: ActiveSpaceConfig = Field(default_factory=ActiveSpaceConfig)
    vqe: VQEConfig = Field(default_factory=VQEConfig)
    noise: NoiseConfig = Field(default_factory=NoiseConfig)

    mapping_method: str = "jordan_wigner"  # Options: 'jordan_wigner', 'parity'
    cache_dir: Path = Path("artifacts/quantum/cache")
    hamiltonians_dir: Path = Path("quantum/hamiltonians")
    
    # Output file paths
    output_results_parquet: Path = Path("quantum/quantum_results.parquet")
    output_vqe_history_parquet: Path = Path("quantum/vqe_history.parquet")
    output_quantum_manifest: Path = Path("quantum/quantum_manifest.json")
    output_active_space_manifest: Path = Path("quantum/active_space_manifest.json")
