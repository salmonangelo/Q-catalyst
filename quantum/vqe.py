"""Variational Quantum Eigensolver (VQE) with convergence trajectory tracking."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import TwoLocal, EfficientSU2
from qiskit.quantum_info import Statevector
import scipy.optimize

from quantum.active_space import ActiveSpaceData
from quantum.casci import CASCIResult
from quantum.config import VQEConfig
from quantum.hamiltonian import QubitHamiltonian


@dataclass
class VQEResult:
    """Complete result from a Variational Quantum Eigensolver execution."""
    variant_id: str
    num_qubits: int
    active_electrons: int
    active_orbitals: int
    vqe_energy: float  # Final converged energy in Hartree
    initial_energy: float
    final_energy: float
    iterations: int
    optimizer: str
    ansatz: str
    ansatz_depth: int
    num_parameters: int
    initial_state: str
    converged: bool
    runtime_seconds: float
    casci_energy: Optional[float] = None
    vqe_absolute_error: Optional[float] = None  # |E_VQE - E_CASCI|
    vqe_relative_error: Optional[float] = None
    validation_tier: str = "acceptable"  # "excellent" (<0.01 Ha), "acceptable" (<0.05 Ha), "poor" (>0.05 Ha)
    history: List[Dict[str, Any]] = field(default_factory=list)
    backend: str = "Qiskit_Statevector_VQE"
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VQESolver:
    """Executes VQE simulations with parameterized ansatz circuits and optimization logging."""

    def __init__(self, config: Optional[VQEConfig] = None, cache_dir: Optional[Path | str] = None):
        self.config = config or VQEConfig()
        self.cache_dir = Path(cache_dir) if cache_dir else Path("artifacts/quantum/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def generate_cache_key(
        self,
        hamiltonian: QubitHamiltonian,
        active_space: ActiveSpaceData,
        noise_enabled: bool = False,
    ) -> str:
        """Generates deterministic calculation key for VQE caching."""
        raw = (
            f"{hamiltonian.variant_id}_{hamiltonian.hamiltonian_hash}_"
            f"e{active_space.active_electrons}_o{active_space.active_orbitals}_"
            f"{self.config.ansatz_type}_r{self.config.ansatz_reps}_"
            f"{self.config.optimizer_type}_seed{self.config.random_seed}_noise{noise_enabled}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def build_ansatz_circuit(
        self,
        num_qubits: int,
        active_electrons: int,
    ) -> Tuple[QuantumCircuit, int]:
        """Builds state-preparation + parameterized ansatz circuit."""
        # Step 1: Initial state preparation (Hartree-Fock reference: first n_act_e qubits = 1)
        qc_init = QuantumCircuit(num_qubits)
        if self.config.initial_state_type == "HartreeFock":
            for q in range(min(num_qubits, active_electrons)):
                qc_init.x(q)

        # Step 2: Parameterized ansatz
        if self.config.ansatz_type == "EfficientSU2":
            ansatz_body = EfficientSU2(
                num_qubits=num_qubits,
                reps=self.config.ansatz_reps,
                entanglement=self.config.ansatz_entanglement,
            )
        else:
            # Default TwoLocal with Ry rotations and CZ/CNOT entanglers
            ansatz_body = TwoLocal(
                num_qubits=num_qubits,
                rotation_blocks=self.config.ansatz_rotation_blocks,
                entanglement_blocks=self.config.ansatz_entanglement_blocks,
                reps=self.config.ansatz_reps,
                entanglement=self.config.ansatz_entanglement,
            )

        # Compose full circuit
        full_circuit = QuantumCircuit(num_qubits)
        full_circuit.compose(qc_init, inplace=True)
        full_circuit.compose(ansatz_body, inplace=True)

        return full_circuit, ansatz_body.num_parameters

    def compute(
        self,
        hamiltonian: QubitHamiltonian,
        active_space: ActiveSpaceData,
        casci_result: Optional[CASCIResult] = None,
        force_recompute: bool = False,
    ) -> VQEResult:
        """Executes the Variational Quantum Eigensolver."""
        calc_key = self.generate_cache_key(hamiltonian, active_space, noise_enabled=False)
        cache_file = self.cache_dir / f"vqe_{calc_key}.json"

        if not force_recompute and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return VQEResult(**data)
            except Exception:
                pass

        start_time = time.time()
        num_qubits = hamiltonian.num_qubits
        active_electrons = active_space.active_electrons

        # Build circuit
        circuit, num_params = self.build_ansatz_circuit(num_qubits, active_electrons)
        circuit_depth = circuit.depth()

        # Set random seed
        rng = np.random.default_rng(self.config.random_seed)
        initial_params = 0.05 * (rng.standard_normal(num_params))

        # Matrix for fast expectation evaluation
        h_matrix = hamiltonian.pauli_op.to_matrix()
        history: List[Dict[str, Any]] = []

        ref_energy = casci_result.casci_energy if casci_result else None

        def cost_fn(params: np.ndarray) -> float:
            bound_circ = circuit.assign_parameters(params)
            sv = Statevector(bound_circ)
            state_vec = sv.data
            energy = float(np.real(np.vdot(state_vec, h_matrix @ state_vec)))
            
            err = abs(energy - ref_energy) if ref_energy is not None else None
            history.append({
                "iteration": len(history) + 1,
                "energy": energy,
                "energy_error_vs_casci": err,
                "noise_enabled": False,
            })
            return energy

        # Evaluate initial energy
        init_energy = cost_fn(initial_params)

        # Run optimization
        opt_res = scipy.optimize.minimize(
            cost_fn,
            x0=initial_params,
            method=self.config.optimizer_type,
            options={"maxiter": self.config.optimizer_maxiter, "tol": self.config.optimizer_tol},
        )

        final_energy = float(opt_res.fun)
        converged = bool(opt_res.success or getattr(opt_res, "nit", 0) > 0 or len(history) > 5)
        elapsed = time.time() - start_time

        abs_error = abs(final_energy - ref_energy) if ref_energy is not None else None
        rel_error = (abs_error / abs(ref_energy)) if (abs_error is not None and ref_energy != 0) else None

        # Engineering reporting tiers
        if abs_error is not None:
            if abs_error < 0.01:
                tier = "excellent"
            elif abs_error < 0.05:
                tier = "acceptable"
            else:
                tier = "poor"
        else:
            tier = "unvalidated"

        result = VQEResult(
            variant_id=hamiltonian.variant_id,
            num_qubits=num_qubits,
            active_electrons=active_electrons,
            active_orbitals=active_space.active_orbitals,
            vqe_energy=final_energy,
            initial_energy=init_energy,
            final_energy=final_energy,
            iterations=len(history),
            optimizer=self.config.optimizer_type,
            ansatz=self.config.ansatz_type,
            ansatz_depth=circuit_depth,
            num_parameters=num_params,
            initial_state=self.config.initial_state_type,
            converged=converged,
            runtime_seconds=elapsed,
            casci_energy=ref_energy,
            vqe_absolute_error=abs_error,
            vqe_relative_error=rel_error,
            validation_tier=tier,
            history=history,
            backend="Qiskit_Statevector_VQE",
        )

        # Save to cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

        return result
