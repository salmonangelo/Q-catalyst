"""Geometry validation, sanity checks, and clash detection for molecular clusters."""

from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np

from chemistry.cluster import ReducedCluster

VALID_ELEMENTS = {"H", "C", "N", "O", "S", "P", "F", "CL", "BR", "I"}
MIN_INTERATOMIC_DISTANCE = 0.50  # Angstroms (anything smaller is severe steric overlap / clash)
MAX_BOND_DISTANCE_C_C = 2.50     # Angstroms for covalent connectivity check


@dataclass
class GeometryValidationResult:
    """Result of structural validation for an electronic-structure calculation cluster."""
    is_valid: bool
    geometry_status: str  # "valid", "warning", "invalid"
    atom_count: int
    min_pairwise_distance: float
    max_pairwise_distance: float
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class GeometryValidator:
    """Validates Cartesian coordinates and atomic topology before quantum/classical chemistry runs."""

    def __init__(
        self,
        min_distance_angstrom: float = MIN_INTERATOMIC_DISTANCE,
        allowed_elements: set[str] | None = None,
    ):
        self.min_distance = min_distance_angstrom
        self.allowed_elements = allowed_elements or VALID_ELEMENTS

    def validate(self, cluster: ReducedCluster) -> GeometryValidationResult:
        """Runs thorough geometric validation on a ReducedCluster."""
        issues: List[str] = []
        warnings: List[str] = []

        atom_count = cluster.atom_count
        if atom_count == 0:
            return GeometryValidationResult(
                is_valid=False,
                geometry_status="invalid",
                atom_count=0,
                min_pairwise_distance=0.0,
                max_pairwise_distance=0.0,
                issues=["Cluster contains 0 atoms."],
            )

        coords = cluster.coordinates
        elements = cluster.elements

        # 1. Check for NaN or Inf coordinates
        if np.isnan(coords).any():
            issues.append("Coordinates contain NaN values.")
        if np.isinf(coords).any():
            issues.append("Coordinates contain Infinite values.")

        # 2. Check element symbols
        for i, elem in enumerate(elements):
            if elem.upper() not in self.allowed_elements:
                issues.append(f"Atom {i} has invalid element symbol '{elem}'.")

        # 3. Pairwise distance checks
        min_dist = float("inf")
        max_dist = 0.0

        if atom_count > 1 and len(issues) == 0:
            # Pairwise distance matrix
            diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
            dist_matrix = np.sqrt(np.sum(diff ** 2, axis=-1))

            # Mask diagonal (self-distance)
            np.fill_diagonal(dist_matrix, np.inf)
            min_dist = float(np.min(dist_matrix))
            max_dist = float(np.max(np.where(dist_matrix == np.inf, 0, dist_matrix)))

            if min_dist < self.min_distance:
                issues.append(
                    f"Severe steric clash: Minimum interatomic distance is {min_dist:.3f} Å "
                    f"(< {self.min_distance:.2f} Å threshold)."
                )
            elif min_dist < 0.85:
                warnings.append(
                    f"Short interatomic distance detected: {min_dist:.3f} Å (possible compression)."
                )

        if issues:
            status = "invalid"
            is_valid = False
        elif warnings:
            status = "warning"
            is_valid = True
        else:
            status = "valid"
            is_valid = True

        return GeometryValidationResult(
            is_valid=is_valid,
            geometry_status=status,
            atom_count=atom_count,
            min_pairwise_distance=min_dist if min_dist != float("inf") else 0.0,
            max_pairwise_distance=max_dist,
            issues=issues,
            warnings=warnings,
        )
