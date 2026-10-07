"""Active-space reduction and orbital selection for quantum chemical simulation."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from quantum.config import ActiveSpaceConfig


@dataclass
class ActiveSpaceData:
    """Represents a validated active-space electronic problem."""
    variant_id: str
    active_electrons: int
    active_orbitals: int
    num_spin_orbitals: int
    orbital_indices: List[int]
    orbital_energies: List[float]
    core_energy: float
    h1_integrals: np.ndarray  # Shape: (active_orbitals, active_orbitals)
    h2_integrals: np.ndarray  # Shape: (active_orbitals, active_orbitals, active_orbitals, active_orbitals)
    selection_method: str
    charge: int
    multiplicity: int
    backend_used: str  # "pyscf", "classical_fallback", "test_fixture"

    def to_manifest_dict(self) -> Dict[str, Any]:
        """Converts active space metadata into JSON-serializable dictionary."""
        return {
            "variant_id": self.variant_id,
            "active_electrons": self.active_electrons,
            "active_orbitals": self.active_orbitals,
            "num_spin_orbitals": self.num_spin_orbitals,
            "orbital_indices": self.orbital_indices,
            "orbital_energies": [float(e) for e in self.orbital_energies],
            "core_energy": float(self.core_energy),
            "selection_method": self.selection_method,
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "backend_used": self.backend_used,
            "h1_shape": list(self.h1_integrals.shape),
            "h2_shape": list(self.h2_integrals.shape),
        }


class ActiveSpaceSelector:
    """Constructs and validates the reduced active space from electronic structure data."""

    def __init__(self, config: Optional[ActiveSpaceConfig] = None):
        self.config = config or ActiveSpaceConfig()

    def validate_active_space(
        self,
        active_electrons: int,
        active_orbitals: int,
        charge: int,
        multiplicity: int,
        h1: np.ndarray,
        h2: np.ndarray,
    ) -> None:
        """Validates physical and dimensional consistency of the active space."""
        if active_orbitals <= 0:
            raise ValueError(f"Active orbitals must be > 0, got {active_orbitals}")
        if active_electrons <= 0:
            raise ValueError(f"Active electrons must be > 0, got {active_electrons}")
        if active_electrons > 2 * active_orbitals:
            raise ValueError(
                f"Active electrons ({active_electrons}) exceeds maximum orbital capacity ({2 * active_orbitals})"
            )

        # Spin compatibility
        spin_s = (multiplicity - 1) / 2.0
        min_electrons_for_spin = int(2 * spin_s)
        if active_electrons < min_electrons_for_spin:
            raise ValueError(
                f"Active electrons ({active_electrons}) incompatible with multiplicity {multiplicity}"
            )

        # Integral dimensions
        if h1.shape != (active_orbitals, active_orbitals):
            raise ValueError(
                f"1-body integrals shape {h1.shape} does not match (active_orbitals, active_orbitals): ({active_orbitals}, {active_orbitals})"
            )
        if h2.shape != (active_orbitals, active_orbitals, active_orbitals, active_orbitals):
            raise ValueError(
                f"2-body integrals shape {h2.shape} does not match ({active_orbitals}, {active_orbitals}, {active_orbitals}, {active_orbitals})"
            )

    def select_active_space(
        self,
        variant_id: str,
        total_electrons: int,
        mo_energies: np.ndarray,
        h1_full: np.ndarray,
        h2_full: np.ndarray,
        core_energy: float = 0.0,
        charge: int = 0,
        multiplicity: int = 1,
        backend_used: str = "classical_fallback",
    ) -> ActiveSpaceData:
        """Selects active frontier orbitals around the Fermi level (HOMO-LUMO)."""
        n_act_e = self.config.active_electrons
        n_act_o = self.config.active_orbitals

        n_mo = len(mo_energies)
        if n_act_o > n_mo:
            raise ValueError(
                f"Requested active orbitals ({n_act_o}) exceeds total molecular orbitals ({n_mo})"
            )

        # Determine HOMO index (0-indexed)
        n_occ = max(1, min(n_mo - 1, total_electrons // 2))
        homo_idx = n_occ - 1

        # Select n_act_e // 2 occupied orbitals below HOMO and remainder above LUMO
        n_occ_act = n_act_e // 2
        n_virt_act = n_act_o - n_occ_act

        start_idx = max(0, homo_idx - n_occ_act + 1)
        end_idx = start_idx + n_act_o
        if end_idx > n_mo:
            end_idx = n_mo
            start_idx = max(0, end_idx - n_act_o)

        chosen_indices = list(range(start_idx, end_idx))
        if len(chosen_indices) != n_act_o:
            raise ValueError(
                f"Could not select {n_act_o} contiguous frontier orbitals from {n_mo} total MOs."
            )

        # Slice 1-body and 2-body active integrals
        idx_grid = np.ix_(chosen_indices, chosen_indices)
        h1_act = h1_full[idx_grid].copy()

        idx_4d = np.ix_(chosen_indices, chosen_indices, chosen_indices, chosen_indices)
        h2_act = h2_full[idx_4d].copy()

        # Validate
        self.validate_active_space(
            active_electrons=n_act_e,
            active_orbitals=n_act_o,
            charge=charge,
            multiplicity=multiplicity,
            h1=h1_act,
            h2=h2_act,
        )

        return ActiveSpaceData(
            variant_id=variant_id,
            active_electrons=n_act_e,
            active_orbitals=n_act_o,
            num_spin_orbitals=2 * n_act_o,
            orbital_indices=chosen_indices,
            orbital_energies=[float(mo_energies[i]) for i in chosen_indices],
            core_energy=float(core_energy),
            h1_integrals=h1_act,
            h2_integrals=h2_act,
            selection_method=f"frontier_homo_lumo_[{start_idx}:{end_idx}]",
            charge=charge,
            multiplicity=multiplicity,
            backend_used=backend_used,
        )

    def create_synthetic_model_active_space(
        self,
        variant_id: str,
        n_electrons: int = 4,
        n_orbitals: int = 4,
        core_energy: float = -15.0,
        charge: int = 0,
        multiplicity: int = 1,
        seed: int = 42,
    ) -> ActiveSpaceData:
        """Constructs a scientifically well-conditioned model (4e, 4o) active space for verification."""
        rng = np.random.default_rng(seed)
        
        # 1-electron diagonal energies with negative eigenvalues
        mo_energies = np.linspace(-1.2, 0.4, n_orbitals)
        h1 = np.diag(mo_energies)
        # Add small symmetric off-diagonal hopping terms
        for i in range(n_orbitals):
            for j in range(i + 1, n_orbitals):
                val = 0.08 / (1.0 + abs(i - j))
                h1[i, j] = val
                h1[j, i] = val

        # 2-electron Coulomb and exchange repulsion tensor
        h2 = np.zeros((n_orbitals, n_orbitals, n_orbitals, n_orbitals), dtype=float)
        for p in range(n_orbitals):
            for q in range(n_orbitals):
                # Coulomb term (p p | q q)
                coulomb = 0.35 / (1.0 + 0.5 * abs(p - q))
                h2[p, p, q, q] = coulomb
                # Exchange term (p q | q p)
                exchange = 0.12 / (1.0 + abs(p - q))
                h2[p, q, q, p] = exchange

        return ActiveSpaceData(
            variant_id=variant_id,
            active_electrons=n_electrons,
            active_orbitals=n_orbitals,
            num_spin_orbitals=2 * n_orbitals,
            orbital_indices=list(range(n_orbitals)),
            orbital_energies=[float(e) for e in mo_energies],
            core_energy=float(core_energy),
            h1_integrals=h1,
            h2_integrals=h2,
            selection_method="model_synthetic_active_space",
            charge=charge,
            multiplicity=multiplicity,
            backend_used="classical_fallback",
        )
