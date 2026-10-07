"""Second-quantized fermionic Hamiltonian construction and Jordan-Wigner qubit mapping."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from qiskit.quantum_info import SparsePauliOp

from quantum.active_space import ActiveSpaceData


@dataclass
class QubitHamiltonian:
    """Represents a qubit-mapped molecular Hamiltonian."""
    variant_id: str
    num_qubits: int
    num_spin_orbitals: int
    num_pauli_terms: int
    constant_energy: float
    hamiltonian_hash: str
    pauli_op: SparsePauliOp
    one_body_terms_count: int
    two_body_terms_count: int
    mapping_method: str = "jordan_wigner"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes metadata and non-zero Pauli terms into JSON-serializable dictionary."""
        pauli_strings = [str(term.to_label()) for term in self.pauli_op.paulis]
        coeffs = [float(np.real(c)) for c in self.pauli_op.coeffs]
        
        return {
            "variant_id": self.variant_id,
            "num_qubits": self.num_qubits,
            "num_spin_orbitals": self.num_spin_orbitals,
            "num_pauli_terms": self.num_pauli_terms,
            "constant_energy": self.constant_energy,
            "hamiltonian_hash": self.hamiltonian_hash,
            "mapping_method": self.mapping_method,
            "one_body_terms_count": self.one_body_terms_count,
            "two_body_terms_count": self.two_body_terms_count,
            "pauli_terms": list(zip(pauli_strings, coeffs)),
        }

    def save_json(self, output_path: Path | str) -> Path:
        """Saves Hamiltonian artifact to disk."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return p


class HamiltonianBuilder:
    """Builds fermionic second-quantized operators and executes Jordan-Wigner qubit mapping."""

    def __init__(self, mapping_method: str = "jordan_wigner"):
        self.mapping_method = mapping_method

    def _make_pauli_string(self, n_qubits: int, specs: List[Tuple[int, str]]) -> str:
        """Generates a Qiskit Pauli string with specified single-qubit operators."""
        # Qiskit Pauli string indexing is from right (qubit 0) to left (qubit N-1)
        chars = ["I"] * n_qubits
        for q, op in specs:
            chars[n_qubits - 1 - q] = op.upper()
        return "".join(chars)

    def build_qubit_hamiltonian(self, active_space: ActiveSpaceData) -> QubitHamiltonian:
        """Constructs the Jordan-Wigner mapped qubit Hamiltonian from active space integrals."""
        n_orb = active_space.active_orbitals
        n_qubits = 2 * n_orb  # Alpha and beta spin-orbitals
        h1 = active_space.h1_integrals
        h2 = active_space.h2_integrals
        e_core = active_space.core_energy

        pauli_dict: Dict[str, float] = {}

        def add_term(pauli_str: str, coeff: float):
            if abs(coeff) > 1e-12:
                pauli_dict[pauli_str] = pauli_dict.get(pauli_str, 0.0) + coeff

        # 1. Core / Nuclear Energy Constant -> Identity operator
        ident_str = "I" * n_qubits
        add_term(ident_str, e_core)

        one_body_count = 0
        two_body_count = 0

        # 2. One-Body Terms: sum_{p,q, sigma} h_{pq} a_{p,sigma}^\dagger a_{q,sigma}
        for p in range(n_orb):
            for q in range(n_orb):
                h_val = float(h1[p, q])
                if abs(h_val) < 1e-12:
                    continue

                for spin in (0, 1):  # 0 for alpha (2p), 1 for beta (2p+1)
                    p_spin = 2 * p + spin
                    q_spin = 2 * q + spin

                    if p_spin == q_spin:
                        # a_p^\dagger a_p = 1/2 (I - Z_p)
                        add_term(ident_str, 0.5 * h_val)
                        z_str = self._make_pauli_string(n_qubits, [(p_spin, "Z")])
                        add_term(z_str, -0.5 * h_val)
                        one_body_count += 1
                    elif p_spin < q_spin:
                        # a_p^\dagger a_q + a_q^\dagger a_p = 1/2 (X_p Z...Z X_q + Y_p Z...Z Y_q)
                        z_indices = list(range(p_spin + 1, q_spin))
                        
                        # XX term
                        xx_specs = [(p_spin, "X"), (q_spin, "X")] + [(k, "Z") for k in z_indices]
                        add_term(self._make_pauli_string(n_qubits, xx_specs), 0.5 * h_val)

                        # YY term
                        yy_specs = [(p_spin, "Y"), (q_spin, "Y")] + [(k, "Z") for k in z_indices]
                        add_term(self._make_pauli_string(n_qubits, yy_specs), 0.5 * h_val)
                        one_body_count += 2

        # 3. Two-Body Terms: 1/2 sum_{p,q,r,s, sigma, tau} g_{pqrs} a_{p,sigma}^\dagger a_{r,tau}^\dagger a_{s,tau} a_{q,sigma}
        # For active space MVP: dominant Coulomb (p p | q q) and Exchange (p q | q p) terms
        for p in range(n_orb):
            for q in range(n_orb):
                coulomb_val = float(h2[p, p, q, q])
                if abs(coulomb_val) > 1e-12:
                    # Coulomb interaction between spin-orbitals
                    for spin_p in (0, 1):
                        for spin_q in (0, 1):
                            p_spin = 2 * p + spin_p
                            q_spin = 2 * q + spin_q
                            if p_spin < q_spin:
                                # n_p n_q = 1/4 (I - Z_p - Z_q + Z_p Z_q)
                                coeff = 0.5 * coulomb_val
                                add_term(ident_str, 0.25 * coeff)
                                add_term(self._make_pauli_string(n_qubits, [(p_spin, "Z")]), -0.25 * coeff)
                                add_term(self._make_pauli_string(n_qubits, [(q_spin, "Z")]), -0.25 * coeff)
                                add_term(self._make_pauli_string(n_qubits, [(p_spin, "Z"), (q_spin, "Z")]), 0.25 * coeff)
                                two_body_count += 4

                if p != q:
                    exch_val = float(h2[p, q, q, p])
                    if abs(exch_val) > 1e-12:
                        # Parallel spin exchange interaction (same spin only)
                        for spin in (0, 1):
                            p_spin = 2 * p + spin
                            q_spin = 2 * q + spin
                            if p_spin < q_spin:
                                coeff = -0.5 * exch_val
                                add_term(ident_str, 0.25 * coeff)
                                add_term(self._make_pauli_string(n_qubits, [(p_spin, "Z")]), -0.25 * coeff)
                                add_term(self._make_pauli_string(n_qubits, [(q_spin, "Z")]), -0.25 * coeff)
                                add_term(self._make_pauli_string(n_qubits, [(p_spin, "Z"), (q_spin, "Z")]), 0.25 * coeff)
                                two_body_count += 4

        # Clean and construct Qiskit SparsePauliOp
        clean_terms = [(k, v) for k, v in pauli_dict.items() if abs(v) > 1e-12]
        if not clean_terms:
            clean_terms = [(ident_str, e_core)]

        pauli_strings, coeffs = zip(*clean_terms)
        sparse_op = SparsePauliOp(list(pauli_strings), coeffs=np.array(coeffs, dtype=complex)).simplify()

        # Deterministic Hamiltonian Hash
        hash_lines = [f"{str(p)}:{float(np.real(c)):.8f}" for p, c in zip(sparse_op.paulis, sparse_op.coeffs)]
        hash_lines.sort()
        raw_hash = "\n".join(hash_lines).encode("utf-8")
        h_hash = hashlib.sha256(raw_hash).hexdigest()

        return QubitHamiltonian(
            variant_id=active_space.variant_id,
            num_qubits=n_qubits,
            num_spin_orbitals=n_qubits,
            num_pauli_terms=len(sparse_op),
            constant_energy=float(e_core),
            hamiltonian_hash=h_hash,
            pauli_op=sparse_op,
            one_body_terms_count=one_body_count,
            two_body_terms_count=two_body_count,
            mapping_method=self.mapping_method,
        )
