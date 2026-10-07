"""Output serialization for Phase 4 chemistry results, cluster geometries, and manifest."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from chemistry.cluster import ReducedCluster
from chemistry.descriptors import MechanisticDescriptors
from chemistry.mutation import VariantClusterResult


CHEMISTRY_SCHEMA_COLUMNS = [
    "variant_id",
    "parent_enzyme",
    "mutations",
    "pdb_id",
    "chain_id",
    "cluster_id",
    "cluster_atom_count",
    "cluster_residue_count",
    "geometry_source",
    "geometry_status",
    "charge",
    "multiplicity",
    "method",
    "basis",
    "scf_converged",
    "scf_iterations",
    "total_energy",
    "runtime_seconds",
    "dipole_x",
    "dipole_y",
    "dipole_z",
    "dipole_magnitude",
    "homo_energy",
    "lumo_energy",
    "homo_lumo_gap",
    "reference_energy",
    "delta_energy",
    "calculation_status",
    "failure_reason",
    "data_source",
    "data_quality_flag",
]


class ChemistryOutputWriter:
    """Manages writing of chem_results.parquet, XYZ files, and cluster_manifest.json."""

    def __init__(self, clusters_dir: Path | str = "chemistry/clusters"):
        self.clusters_dir = Path(clusters_dir)
        self.clusters_dir.mkdir(parents=True, exist_ok=True)

    def export_cluster_xyz(self, cluster: ReducedCluster, filename: Optional[str] = None) -> Path:
        """Exports an individual reduced cluster to an XYZ coordinate file."""
        fname = filename or f"{cluster.cluster_id}.xyz"
        out_path = self.clusters_dir / fname
        cluster.save_xyz(out_path)
        return out_path

    def write_cluster_manifest(
        self,
        clusters: List[ReducedCluster],
        output_path: Path | str = "chemistry/clusters/cluster_manifest.json",
    ) -> Path:
        """Writes machine-readable manifest of all generated clusters for downstream Phase 5."""
        manifest_data = {
            "version": "1.0.0",
            "cluster_count": len(clusters),
            "clusters": [
                {
                    "cluster_id": c.cluster_id,
                    "pdb_id": c.pdb_id,
                    "chain_id": c.chain_id,
                    "parent_enzyme": c.parent_enzyme,
                    "residues_included": c.residues_included,
                    "atom_count": c.atom_count,
                    "residue_count": c.residue_count,
                    "geometry_hash": c.geometry_hash,
                    "radius_angstrom": c.radius_angstrom,
                    "center_residue": c.center_residue,
                    "description": c.description,
                    "xyz_file": f"{c.cluster_id}.xyz",
                }
                for c in clusters
            ],
        }
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        return out_file

    def build_results_dataframe(
        self,
        descriptors_list: List[MechanisticDescriptors],
        var_cluster_results: Dict[str, VariantClusterResult],
        data_source: str = "IsPETase_5XJH_Structure",
        data_quality_flag: str = "COMPUTED_CLASSICAL_ELECTRONIC_STRUCTURE",
    ) -> pd.DataFrame:
        """Constructs a strictly typed pandas DataFrame conforming to the chemistry contract."""
        rows = []
        for desc in descriptors_list:
            var_id = desc.variant_id
            v_res = var_cluster_results.get(var_id)

            cluster = v_res.cluster if v_res else None
            mutations = v_res.mutations if v_res else ""
            parent = cluster.parent_enzyme if cluster else "IsPETase"
            pdb_id = cluster.pdb_id if cluster else "5XJH"
            chain_id = cluster.chain_id if cluster else "A"
            cluster_id = cluster.cluster_id if cluster else f"{var_id}_cluster"

            row = {
                "variant_id": str(var_id),
                "parent_enzyme": str(parent),
                "mutations": str(mutations),
                "pdb_id": str(pdb_id),
                "chain_id": str(chain_id),
                "cluster_id": str(cluster_id),
                "cluster_atom_count": int(desc.cluster_atom_count),
                "cluster_residue_count": int(desc.cluster_residue_count),
                "geometry_source": str(desc.geometry_source),
                "geometry_status": str(desc.geometry_status),
                "charge": int(desc.charge),
                "multiplicity": int(desc.multiplicity),
                "method": str(desc.method),
                "basis": str(desc.basis),
                "scf_converged": bool(desc.scf_converged),
                "scf_iterations": int(desc.scf_iterations),
                "total_energy": float(desc.total_energy) if desc.total_energy is not None else None,
                "runtime_seconds": float(desc.runtime_seconds) if hasattr(desc, "runtime_seconds") else 0.0,
                "dipole_x": float(desc.dipole_x) if desc.dipole_x is not None else None,
                "dipole_y": float(desc.dipole_y) if desc.dipole_y is not None else None,
                "dipole_z": float(desc.dipole_z) if desc.dipole_z is not None else None,
                "dipole_magnitude": float(desc.dipole_magnitude) if desc.dipole_magnitude is not None else None,
                "homo_energy": float(desc.homo_energy) if desc.homo_energy is not None else None,
                "lumo_energy": float(desc.lumo_energy) if desc.lumo_energy is not None else None,
                "homo_lumo_gap": float(desc.homo_lumo_gap) if desc.homo_lumo_gap is not None else None,
                "reference_energy": float(desc.reference_energy) if desc.reference_energy is not None else None,
                "delta_energy": float(desc.delta_energy) if desc.delta_energy is not None else None,
                "calculation_status": str(desc.calculation_status),
                "failure_reason": str(desc.failure_reason) if desc.failure_reason is not None else None,
                "data_source": str(data_source),
                "data_quality_flag": str(data_quality_flag),
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        # Ensure all contract columns are present
        for col in CHEMISTRY_SCHEMA_COLUMNS:
            if col not in df.columns:
                df[col] = None

        return df[CHEMISTRY_SCHEMA_COLUMNS]

    def save_results_parquet(
        self,
        df: pd.DataFrame,
        output_path: Path | str = "chemistry/chem_results.parquet",
    ) -> Path:
        """Saves chemistry results to Parquet file."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_file, index=False)
        return out_file
