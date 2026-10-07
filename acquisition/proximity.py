"""Active-site structural proximity calculator and mapping engine."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from acquisition.config import ProximityConfig
from data.mutations import SingleMutation, parse_mutations
from data.structure_utils import StructureManager, StructureMappingError


@dataclass(frozen=True)
class ProximityResult:
    """Detailed structural proximity and mapping outcome for a variant."""
    variant_id: str
    mutations: str
    parent_enzyme: str
    min_distance_angstrom: Optional[float]
    proximity_score: Optional[float]
    closest_active_site_residue: Optional[int]
    structure_mapping_status: str  # 'mapped', 'mapped_wt', 'missing_residue', 'numbering_mismatch', 'outside_structure', 'unmapped_parent'
    structure_mapping_reason: str


class ActiveSiteProximityCalculator:
    """Calculates physical 3D distance of variant mutations from IsPETase active-site residues."""

    def __init__(self, config: Optional[ProximityConfig] = None):
        self.config = config or ProximityConfig()
        self.structure_manager: Optional[StructureManager] = None
        self.active_site_positions = set(self.config.active_site_residues)
        self.d0 = self.config.decay_length_angstrom
        self._load_structure()

    def _load_structure(self) -> None:
        """Initialize StructureManager on reference PDB (5XJH)."""
        pdb_path = Path(self.config.reference_pdb_path)
        if pdb_path.exists():
            try:
                self.structure_manager = StructureManager(
                    pdb_file=pdb_path, structure_id="5xjh_ref"
                )
            except Exception as e:
                print(f"Warning: Failed to load PDB structure from {pdb_path}: {e}")
                self.structure_manager = None
        else:
            self.structure_manager = None

    def calculate_proximity(
        self,
        variant_id: str,
        mutations_str: str,
        parent_enzyme: str = "IsPETase",
    ) -> ProximityResult:
        """Compute minimum 3D Euclidean distance from mutation sites to catalytic pocket.

        Args:
            variant_id: Unique variant identifier.
            mutations_str: Canonical mutation string (e.g. S160A;D206G or WT).
            parent_enzyme: Name of parent enzyme scaffold.

        Returns:
            ProximityResult dataclass.
        """
        # Check if reference structure is loaded
        if self.structure_manager is None:
            return ProximityResult(
                variant_id=variant_id,
                mutations=mutations_str,
                parent_enzyme=parent_enzyme,
                min_distance_angstrom=None,
                proximity_score=None,
                closest_active_site_residue=None,
                structure_mapping_status="unmapped_no_structure",
                structure_mapping_reason=f"Reference PDB {self.config.reference_pdb_path} not available.",
            )

        # Non-IsPETase parents require homology mapping
        if parent_enzyme != self.config.reference_parent:
            return ProximityResult(
                variant_id=variant_id,
                mutations=mutations_str,
                parent_enzyme=parent_enzyme,
                min_distance_angstrom=None,
                proximity_score=None,
                closest_active_site_residue=None,
                structure_mapping_status="unmapped_parent",
                structure_mapping_reason=f"Structural coordinates only available for {self.config.reference_parent}; parent {parent_enzyme} unmapped.",
            )

        # Parse mutations
        try:
            muts = parse_mutations(mutations_str)
        except Exception as e:
            return ProximityResult(
                variant_id=variant_id,
                mutations=mutations_str,
                parent_enzyme=parent_enzyme,
                min_distance_angstrom=None,
                proximity_score=None,
                closest_active_site_residue=None,
                structure_mapping_status="parse_error",
                structure_mapping_reason=f"Unparseable mutation string: {e}",
            )

        # Wild-type handling
        if not muts:
            return ProximityResult(
                variant_id=variant_id,
                mutations="WT",
                parent_enzyme=parent_enzyme,
                min_distance_angstrom=0.0,
                proximity_score=1.0,
                closest_active_site_residue=160,
                structure_mapping_status="mapped_wt",
                structure_mapping_reason="Wild-type reference located at catalytic triad center.",
            )

        # Map each point mutation to structure
        chain_id = self.config.reference_chain_id
        chain_residues = self.structure_manager.get_residues_for_chain(chain_id)

        min_dist = float("inf")
        closest_active_res: Optional[int] = None
        mapping_issues: List[str] = []

        for m in muts:
            # 1. Check if position exists in structure
            if m.position not in chain_residues:
                mapping_issues.append(f"Position {m.position} outside resolved chain {chain_id} coordinates.")
                continue

            res_info = chain_residues[m.position]
            if res_info.res_name_1 != m.from_residue:
                mapping_issues.append(
                    f"Residue mismatch at pos {m.position}: structure has {res_info.res_name_1}, mutation specifies {m.from_residue}."
                )
                continue

            if res_info.ca_coord is None:
                mapping_issues.append(f"Residue {m.position} missing CA coordinate.")
                continue

            # 2. Compute distance to all defined active site residues
            m_ca = np.array(res_info.ca_coord)
            for active_pos in self.active_site_positions:
                active_res = chain_residues.get(active_pos)
                if active_res and active_res.ca_coord is not None:
                    dist = float(np.linalg.norm(m_ca - np.array(active_res.ca_coord)))
                    if dist < min_dist:
                        min_dist = dist
                        closest_active_res = active_pos

        # If none of the mutations could be mapped
        if min_dist == float("inf"):
            reason = "; ".join(mapping_issues) if mapping_issues else "No mutations successfully mapped to structure."
            return ProximityResult(
                variant_id=variant_id,
                mutations=mutations_str,
                parent_enzyme=parent_enzyme,
                min_distance_angstrom=None,
                proximity_score=None,
                closest_active_site_residue=None,
                structure_mapping_status="missing_residue" if "outside" in reason else "numbering_mismatch",
                structure_mapping_reason=reason,
            )

        # Smooth exponential proximity decay: S_prox = exp(-d_min / d0)
        # S_prox = 1.0 at d=0, S_prox = 0.368 at d=8A, S_prox = 0.05 at d=24A
        proximity_score = float(np.exp(-min_dist / self.d0))

        status = "mapped"
        reason = f"Closest active site residue: pos {closest_active_res} ({min_dist:.2f} A CA-CA distance)."
        if mapping_issues:
            status = "partially_mapped"
            reason += f" (Note: {'; '.join(mapping_issues)})"

        return ProximityResult(
            variant_id=variant_id,
            mutations=mutations_str,
            parent_enzyme=parent_enzyme,
            min_distance_angstrom=float(min_dist),
            proximity_score=proximity_score,
            closest_active_site_residue=closest_active_res,
            structure_mapping_status=status,
            structure_mapping_reason=reason,
        )

    def calculate_dataframe_proximity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute proximity results for all records in a DataFrame."""
        results = []
        for _, row in df.iterrows():
            var_id = str(row.get("variant_id", ""))
            muts = str(row.get("mutations", "WT"))
            parent = str(row.get("parent_enzyme", "IsPETase"))

            res = self.calculate_proximity(var_id, muts, parent)
            results.append({
                "variant_id": res.variant_id,
                "min_distance_angstrom": res.min_distance_angstrom,
                "proximity_score": res.proximity_score,
                "closest_active_site_residue": res.closest_active_site_residue,
                "structure_mapping_status": res.structure_mapping_status,
                "structure_mapping_reason": res.structure_mapping_reason,
            })

        return pd.DataFrame(results)
