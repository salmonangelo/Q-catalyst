"""Complete Active Space Configuration Interaction (CASCI) exact classical solver."""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.linalg

from quantum.active_space import ActiveSpaceData
from quantum.hamiltonian import QubitHamiltonian


@dataclass
class CASCIResult:
    """Exact classical reference result from CASCI active-space diagonalization."""
    variant_id: str
    active_electrons: int
    active_orbitals: int
    num_qubits: int
    casci_energy: float  # in Hartree
    hartree_fock_energy: Optional[float]
    correlation_energy: Optional[float]  # E_CASCI - E_HF
    converged: bool
    runtime_seconds: float
    backend: str = "ExactDiagonalization_CASCI"
    metadata: Dict[str, Any] = field(default_factory=dict)


class CASCISolver:
    """Solves for exact ground-state eigenvalues of active-space Hamiltonians."""

    def __init__(self):
        pass

    def compute(
        self,
        hamiltonian: QubitHamiltonian,
        active_space: ActiveSpaceData,
    ) -> CASCIResult:
        """Performs exact diagonalization of the active-space qubit Hamiltonian."""
        start_time = time.time()
        n_qubits = hamiltonian.num_qubits
        n_act_e = active_space.active_electrons

        # Build full 2^N x 2^N matrix representation of the Pauli operator
        # For 8 qubits (4e, 4o), matrix is 256x256, solving in <5ms
        h_matrix = hamiltonian.pauli_op.to_matrix()
        dim = 2 ** n_qubits

        # Generate bitmasks for states with exactly n_act_e active electrons
        # (Hamming weight == n_act_e)
        valid_basis_indices = []
        for i in range(dim):
            # Count set bits in integer i
            if bin(i).count("1") == n_act_e:
                valid_basis_indices.append(i)

        if valid_basis_indices:
            # Subspace projection onto particle-conserving sector
            sub_idx = np.array(valid_basis_indices, dtype=int)
            h_sub = h_matrix[np.ix_(sub_idx, sub_idx)]
            eigvals, eigvecs = scipy.linalg.eigh(h_sub)
            casci_e = float(eigvals[0])
        else:
            # Full Hilbert space diagonalization fallback
            eigvals, eigvecs = scipy.linalg.eigh(h_matrix)
            casci_e = float(eigvals[0])

        # Evaluate Hartree-Fock reference state energy
        # HF state |11...100...0>: first n_act_e qubits in state |1>
        hf_int = (1 << n_act_e) - 1
        hf_state = np.zeros(dim, dtype=complex)
        hf_state[hf_int] = 1.0
        hf_energy = float(np.real(np.vdot(hf_state, h_matrix @ hf_state)))

        corr_energy = float(casci_e - hf_energy)
        elapsed = time.time() - start_time

        return CASCIResult(
            variant_id=hamiltonian.variant_id,
            active_electrons=active_space.active_electrons,
            active_orbitals=active_space.active_orbitals,
            num_qubits=n_qubits,
            casci_energy=casci_e,
            hartree_fock_energy=hf_energy,
            correlation_energy=corr_energy,
            converged=True,
            runtime_seconds=elapsed,
            backend="ExactDiagonalization_CASCI",
            metadata={
                "subspace_dimension": len(valid_basis_indices),
                "full_dimension": dim,
                "hamiltonian_hash": hamiltonian.hamiltonian_hash,
            },
        )
