"""Mechanistic descriptor extraction and wild-type relative delta energy analysis."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np

from chemistry.cluster import ReducedCluster
from chemistry.electronic_structure import ElectronicStructureResult
from chemistry.mutation import VariantClusterResult


@dataclass
class MechanisticDescriptors:
    """Consolidated mechanistic and electronic descriptors for a variant cluster."""
    variant_id: str
    total_energy: Optional[float]
    reference_energy: Optional[float]
    delta_energy: Optional[float]  # E_variant - E_ref (Hartree)
    dipole_x: Optional[float]
    dipole_y: Optional[float]
    dipole_z: Optional[float]
    dipole_magnitude: Optional[float]
    homo_energy: Optional[float]
    lumo_energy: Optional[float]
    homo_lumo_gap: Optional[float]
    catalytic_triad_ser_his_dist: Optional[float]  # Ser160 to His237 distance in Å
    catalytic_triad_his_asp_dist: Optional[float]  # His237 to Asp206 distance in Å
    min_mutation_distance_to_active_site: Optional[float]
    cluster_atom_count: int
    cluster_residue_count: int
    geometry_source: str
    geometry_status: str
    scf_converged: bool
    scf_iterations: int
    runtime_seconds: float
    calculation_status: str
    failure_reason: Optional[str]
    method: str
    basis: str
    charge: int
    multiplicity: int


class DescriptorExtractor:
    """Extracts mechanistic electronic, geometric, and energetic descriptors."""

    def __init__(self):
        pass

    def _find_atom_coord(self, cluster: ReducedCluster, res_seq: int, atom_name: str) -> Optional[np.ndarray]:
        for atom in cluster.atoms:
            if atom.res_seq == res_seq and atom.atom_name == atom_name:
                return atom.coord
        # Fallback to CA
        for atom in cluster.atoms:
            if atom.res_seq == res_seq and atom.atom_name == "CA":
                return atom.coord
        return None

    def calculate_triad_distances(self, cluster: ReducedCluster) -> Tuple[Optional[float], Optional[float]]:
        """Calculates key distances within the catalytic triad (Ser160 - His237 - Asp206)."""
        ser_coord = self._find_atom_coord(cluster, 160, "OG")
        if ser_coord is None:
            ser_coord = self._find_atom_coord(cluster, 160, "CA")

        his_coord = self._find_atom_coord(cluster, 237, "NE2")
        if his_coord is None:
            his_coord = self._find_atom_coord(cluster, 237, "CA")

        asp_coord = self._find_atom_coord(cluster, 206, "OD1")
        if asp_coord is None:
            asp_coord = self._find_atom_coord(cluster, 206, "CA")

        ser_his_dist = (
            float(np.linalg.norm(ser_coord - his_coord))
            if (ser_coord is not None and his_coord is not None)
            else None
        )
        his_asp_dist = (
            float(np.linalg.norm(his_coord - asp_coord))
            if (his_coord is not None and asp_coord is not None)
            else None
        )

        return ser_his_dist, his_asp_dist

    def extract(
        self,
        var_cluster_result: VariantClusterResult,
        elec_result: ElectronicStructureResult,
        ref_elec_result: Optional[ElectronicStructureResult] = None,
    ) -> MechanisticDescriptors:
        """Extracts complete descriptors with reference baseline comparison."""
        cluster = var_cluster_result.cluster
        ser_his, his_asp = self.calculate_triad_distances(cluster)

        # Reference energy comparison: only if reference is converged and calculated under compatible protocol
        ref_energy = None
        delta_energy = None

        if ref_elec_result and ref_elec_result.scf_converged and ref_elec_result.total_energy is not None:
            # Verify protocol compatibility
            if (
                ref_elec_result.method == elec_result.method
                and ref_elec_result.basis == elec_result.basis
                and ref_elec_result.charge == elec_result.charge
                and ref_elec_result.multiplicity == elec_result.multiplicity
            ):
                ref_energy = ref_elec_result.total_energy
                if elec_result.scf_converged and elec_result.total_energy is not None:
                    delta_energy = float(elec_result.total_energy - ref_energy)

        # Min distance from mutations to active site
        min_mut_dist = None
        if var_cluster_result.mutation_distances:
            min_mut_dist = min(var_cluster_result.mutation_distances.values())

        return MechanisticDescriptors(
            variant_id=var_cluster_result.variant_id,
            total_energy=elec_result.total_energy,
            reference_energy=ref_energy,
            delta_energy=delta_energy,
            dipole_x=elec_result.dipole_x,
            dipole_y=elec_result.dipole_y,
            dipole_z=elec_result.dipole_z,
            dipole_magnitude=elec_result.dipole_magnitude,
            homo_energy=elec_result.homo_energy,
            lumo_energy=elec_result.lumo_energy,
            homo_lumo_gap=elec_result.homo_lumo_gap,
            catalytic_triad_ser_his_dist=ser_his,
            catalytic_triad_his_asp_dist=his_asp,
            min_mutation_distance_to_active_site=min_mut_dist,
            cluster_atom_count=cluster.atom_count,
            cluster_residue_count=cluster.residue_count,
            geometry_source=var_cluster_result.geometry_source,
            geometry_status=elec_result.geometry_status,
            scf_converged=elec_result.scf_converged,
            scf_iterations=elec_result.scf_iterations,
            runtime_seconds=elec_result.runtime_seconds,
            calculation_status=elec_result.calculation_status,
            failure_reason=elec_result.failure_reason,
            method=elec_result.method,
            basis=elec_result.basis,
            charge=elec_result.charge,
            multiplicity=elec_result.multiplicity,
        )
