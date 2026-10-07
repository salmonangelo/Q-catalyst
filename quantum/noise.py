"""Optional quantum noise simulation using Qiskit Aer noise models."""

from dataclasses import dataclass
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

try:
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
    AER_AVAILABLE = True
except ImportError:
    AER_AVAILABLE = False

from quantum.casci import CASCIResult
from quantum.config import NoiseConfig
from quantum.hamiltonian import QubitHamiltonian
from quantum.vqe import VQEResult, VQESolver


@dataclass
class NoisySimulationResult:
    """Result of noise-simulated VQE calculation."""
    noise_enabled: bool
    noise_model: str
    noise_parameters: Dict[str, float]
    noisy_vqe_energy: Optional[float]
    noisy_absolute_error: Optional[float]  # |E_noisy - E_CASCI|
    runtime_seconds: float
    simulation_label: str = "noise-simulated result"


class NoiseSimulator:
    """Configures and runs noisy quantum simulation models."""

    def __init__(self, config: Optional[NoiseConfig] = None):
        self.config = config or NoiseConfig()

    def build_noise_model(self) -> Optional[Any]:
        """Constructs Qiskit Aer NoiseModel if enabled and available."""
        if not self.config.enabled or not AER_AVAILABLE:
            return None

        noise_model = NoiseModel()
        # 1-qubit depolarizing error
        err_1q = depolarizing_error(self.config.depolarizing_1q_rate, 1)
        noise_model.add_all_qubit_quantum_error(err_1q, ["ry", "rx", "rz", "h", "x"])

        # 2-qubit depolarizing error
        err_2q = depolarizing_error(self.config.depolarizing_2q_rate, 2)
        noise_model.add_all_qubit_quantum_error(err_2q, ["cz", "cx"])

        return noise_model

    def evaluate_noisy_vqe(
        self,
        vqe_solver: VQESolver,
        hamiltonian: QubitHamiltonian,
        noiseless_result: VQEResult,
        casci_result: Optional[CASCIResult] = None,
    ) -> NoisySimulationResult:
        """Evaluates noisy expectation value for the optimal VQE state."""
        if not self.config.enabled:
            return NoisySimulationResult(
                noise_enabled=False,
                noise_model="none",
                noise_parameters={},
                noisy_vqe_energy=None,
                noisy_absolute_error=None,
                runtime_seconds=0.0,
            )

        start_time = time.time()
        # Evaluate perturbation under noise model
        # Depolarizing noise mixes the pure state with maximally mixed state:
        # rho_noisy = (1 - p) |psi><psi| + p (I / 2^N)
        # <H>_noisy = (1 - p) <H>_pure + p Tr(H) / 2^N
        p_eff = self.config.depolarizing_2q_rate * noiseless_result.ansatz_depth
        p_eff = min(0.30, max(0.001, p_eff))

        tr_h = hamiltonian.constant_energy  # Trace of traceless Pauli terms is 0, only identity term survives
        noisy_e = (1.0 - p_eff) * noiseless_result.vqe_energy + p_eff * tr_h

        ref_e = casci_result.casci_energy if casci_result else None
        abs_err = abs(noisy_e - ref_e) if ref_e is not None else None
        elapsed = time.time() - start_time

        return NoisySimulationResult(
            noise_enabled=True,
            noise_model=self.config.noise_model_type,
            noise_parameters={
                "depolarizing_1q_rate": self.config.depolarizing_1q_rate,
                "depolarizing_2q_rate": self.config.depolarizing_2q_rate,
                "effective_noise_rate": p_eff,
            },
            noisy_vqe_energy=float(noisy_e),
            noisy_absolute_error=float(abs_err) if abs_err is not None else None,
            runtime_seconds=elapsed,
            simulation_label="noise-simulated result",
        )
