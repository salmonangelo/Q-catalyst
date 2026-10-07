"""Q-Catalyst Phase 5: Quantum Simulation Layer.

Provides active-space reduction, Jordan-Wigner Hamiltonian construction,
CASCI exact reference diagonalization, Variational Quantum Eigensolver (VQE),
optional noise modeling, and reproducible result serialization.
"""

from quantum.active_space import ActiveSpaceData, ActiveSpaceSelector
from quantum.casci import CASCIResult, CASCISolver
from quantum.config import (
    ActiveSpaceConfig,
    NoiseConfig,
    QuantumConfig,
    VQEConfig,
)
from quantum.evaluate import QuantumPipeline
from quantum.hamiltonian import HamiltonianBuilder, QubitHamiltonian
from quantum.noise import NoiseSimulator, NoisySimulationResult
from quantum.outputs import (
    QUANTUM_RESULTS_SCHEMA_COLUMNS,
    QuantumOutputWriter,
    VQE_HISTORY_SCHEMA_COLUMNS,
)
from quantum.vqe import VQEResult, VQESolver

__all__ = [
    "ActiveSpaceConfig",
    "ActiveSpaceData",
    "ActiveSpaceSelector",
    "CASCIResult",
    "CASCISolver",
    "HamiltonianBuilder",
    "NoiseConfig",
    "NoiseSimulator",
    "NoisySimulationResult",
    "QUANTUM_RESULTS_SCHEMA_COLUMNS",
    "QuantumConfig",
    "QuantumOutputWriter",
    "QuantumPipeline",
    "QubitHamiltonian",
    "VQE_HISTORY_SCHEMA_COLUMNS",
    "VQEConfig",
    "VQEResult",
    "VQESolver",
]
