"""PDB structural parser and atom-level coordinate extraction for enzyme active sites."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import numpy as np

try:
    from Bio.PDB import PDBParser
    from Bio.PDB.Polypeptide import protein_letters_3to1
except ImportError:
    PDBParser = None
    protein_letters_3to1 = {}


@dataclass(frozen=True)
class AtomCoord:
    """Represents a single 3D atom with coordinates, element, and residue context."""
    atom_name: str
    element: str
    x: float
    y: float
    z: float
    res_name: str
    res_seq: int
    chain_id: str
    occupancy: float = 1.0
    bfactor: float = 0.0

    @property
    def coord_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=float)


@dataclass
class ResidueAtoms:
    """Collection of all atoms belonging to a specific amino acid residue."""
    res_name: str
    res_seq: int
    chain_id: str
    atoms: List[AtomCoord] = field(default_factory=list)

    @property
    def ca_atom(self) -> Optional[AtomCoord]:
        for a in self.atoms:
            if a.atom_name == "CA":
                return a
        return None

    @property
    def atom_names(self) -> List[str]:
        return [a.atom_name for a in self.atoms]


class StructureReader:
    """Reads crystallographic PDB files and provides atom-level queries for Chain A."""

    def __init__(self, pdb_path: Path | str, chain_id: str = "A"):
        self.pdb_path = Path(pdb_path)
        self.chain_id = chain_id
        self.residues: Dict[int, ResidueAtoms] = {}
        self.metadata: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.pdb_path.exists():
            raise FileNotFoundError(f"PDB structure not found at: {self.pdb_path}")

        if PDBParser is None:
            raise ImportError("biopython is required for structure parsing.")

        parser = PDBParser(QUIET=True)
        structure = parser.get_structure("chem_ref", str(self.pdb_path))

        self.metadata = {
            "pdb_id": self.pdb_path.stem.upper(),
            "chain_id": self.chain_id,
            "structure_file": str(self.pdb_path),
            "structure_source": "RCSB_PDB_XRAY",
        }

        for model in structure:
            for chain in model:
                if chain.id != self.chain_id:
                    continue

                for res in chain:
                    hetflag, resseq, icode = res.get_id()
                    if hetflag.strip() != "":
                        continue  # Skip waters and heteroatoms

                    res_name_3 = res.get_resname().strip().upper()
                    res_entry = ResidueAtoms(
                        res_name=res_name_3,
                        res_seq=resseq,
                        chain_id=self.chain_id,
                    )

                    for atom in res:
                        name = atom.get_name().strip()
                        element = atom.element.strip().upper()
                        if not element:
                            # Infer element from atom name
                            element = name[0]
                        coord = atom.get_coord()

                        atom_obj = AtomCoord(
                            atom_name=name,
                            element=element,
                            x=float(coord[0]),
                            y=float(coord[1]),
                            z=float(coord[2]),
                            res_name=res_name_3,
                            res_seq=resseq,
                            chain_id=self.chain_id,
                            occupancy=float(atom.get_occupancy() or 1.0),
                            bfactor=float(atom.get_bfactor() or 0.0),
                        )
                        res_entry.atoms.append(atom_obj)

                    self.residues[resseq] = res_entry
            break  # First model only

    def get_residue(self, res_seq: int) -> Optional[ResidueAtoms]:
        return self.residues.get(res_seq)

    def get_residues_subset(self, res_seqs: List[int]) -> Dict[int, ResidueAtoms]:
        return {seq: self.residues[seq] for seq in res_seqs if seq in self.residues}
