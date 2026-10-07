"""Reduced active-site catalytic cluster definition, extraction, and geometry export."""

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

from chemistry.config import ClusterConfig
from chemistry.structure import AtomCoord, ResidueAtoms, StructureReader


@dataclass
class ClusterAtom:
    """An individual atom in the reduced cluster."""
    symbol: str
    x: float
    y: float
    z: float
    res_name: str
    res_seq: int
    atom_name: str
    is_capped_hydrogen: bool = False

    @property
    def coord(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=float)


@dataclass
class ReducedCluster:
    """Scientifically traceable reduced cluster representing the catalytic active site."""
    cluster_id: str
    pdb_id: str
    chain_id: str
    parent_enzyme: str
    residues_included: List[int]
    atoms: List[ClusterAtom] = field(default_factory=list)
    radius_angstrom: float = 6.0
    center_residue: int = 160
    description: str = "Reduced active-site cluster model"

    @property
    def atom_count(self) -> int:
        return len(self.atoms)

    @property
    def residue_count(self) -> int:
        return len(set(a.res_seq for a in self.atoms if not a.is_capped_hydrogen))

    @property
    def elements(self) -> List[str]:
        return [a.symbol for a in self.atoms]

    @property
    def coordinates(self) -> np.ndarray:
        if not self.atoms:
            return np.empty((0, 3), dtype=float)
        return np.array([[a.x, a.y, a.z] for a in self.atoms], dtype=float)

    @property
    def geometry_hash(self) -> str:
        """Deterministic SHA-256 hash of the cluster geometry for caching and traceability."""
        lines = []
        for a in self.atoms:
            # Round coordinates to 4 decimal places for numerical stability across platforms
            lines.append(f"{a.symbol}:{a.x:.4f}:{a.y:.4f}:{a.z:.4f}")
        raw = "\n".join(lines).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def to_xyz_string(self, comment: Optional[str] = None) -> str:
        """Converts cluster to standard XYZ Cartesian coordinate format."""
        num_atoms = len(self.atoms)
        cmt = comment or f"Cluster: {self.cluster_id} | PDB: {self.pdb_id} | At: {num_atoms}"
        lines = [str(num_atoms), cmt]
        for a in self.atoms:
            lines.append(f"{a.symbol:<2}  {a.x:12.6f}  {a.y:12.6f}  {a.z:12.6f}")
        return "\n".join(lines) + "\n"

    def save_xyz(self, output_path: Path | str, comment: Optional[str] = None) -> Path:
        """Saves the cluster to an XYZ coordinate file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_xyz_string(comment=comment), encoding="utf-8")
        return path

    def to_pyscf_mol_string(self) -> str:
        """Formats geometry for PySCF Mole.atom string specification."""
        lines = []
        for a in self.atoms:
            lines.append(f"{a.symbol} {a.x:.6f} {a.y:.6f} {a.z:.6f}")
        return "; ".join(lines)


class ClusterBuilder:
    """Builds reduced active-site clusters from enzyme structure representations."""

    def __init__(self, config: Optional[ClusterConfig] = None):
        self.config = config or ClusterConfig()

    def build_wildtype_cluster(
        self,
        active_site_residues: Dict[int, ResidueAtoms],
        pdb_id: str = "5XJH",
        cluster_id: str = "WT_5XJH_active_site",
    ) -> ReducedCluster:
        """Builds the canonical reduced wild-type cluster from the identified active-site residues."""
        cluster_atoms: List[ClusterAtom] = []

        # Order residues systematically by residue sequence number
        for res_seq in sorted(active_site_residues.keys()):
            res = active_site_residues[res_seq]
            for atom in res.atoms:
                cluster_atoms.append(
                    ClusterAtom(
                        symbol=atom.element,
                        x=atom.x,
                        y=atom.y,
                        z=atom.z,
                        res_name=res.res_name,
                        res_seq=res.res_seq,
                        atom_name=atom.atom_name,
                        is_capped_hydrogen=False,
                    )
                )

        return ReducedCluster(
            cluster_id=cluster_id,
            pdb_id=pdb_id,
            chain_id=self.config.reference_chain_id,
            parent_enzyme=self.config.reference_parent,
            residues_included=sorted(list(active_site_residues.keys())),
            atoms=cluster_atoms,
            radius_angstrom=self.config.cluster_radius_angstrom,
            center_residue=self.config.catalytic_center_residue,
            description="Reduced catalytic active-site cluster containing Ser160-Asp206-His237 triad, oxyanion hole, and substrate cleft",
        )
