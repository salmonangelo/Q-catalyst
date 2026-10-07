"""Structure utility module for PDB loading, residue inspection, and mutation mapping."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

try:
    from Bio.PDB import PDBParser, Selection, Structure
    from Bio.PDB.Polypeptide import protein_letters_3to1
except ImportError:
    PDBParser = None
    Selection = None
    Structure = None
    protein_letters_3to1 = {}

from data.mutations import SingleMutation, parse_mutations


@dataclass(frozen=True)
class ResidueInfo:
    """Detailed structural residue information."""
    chain_id: str
    res_name_3: str
    res_name_1: str
    res_seq: int  # PDB residue sequence number
    insertion_code: str
    is_standard_aa: bool
    ca_coord: Optional[Tuple[float, float, float]] = None


class StructureMappingError(ValueError):
    """Raised when mutation cannot be mapped to the PDB structure."""
    pass


class StructureManager:
    """Manages PDB structure loading, chain inspection, residue numbering, and active site mapping."""

    def __init__(self, pdb_file: Path | str, structure_id: str = "reference"):
        self.pdb_file = Path(pdb_file)
        self.structure_id = structure_id
        self._structure: Optional[Any] = None
        self._residues: Dict[str, Dict[int, ResidueInfo]] = {}  # chain -> {res_seq: ResidueInfo}

        if not self.pdb_file.exists():
            raise FileNotFoundError(
                f"PDB structure file not found: {self.pdb_file}. "
                f"Please download it from RCSB PDB (e.g. 5XJH for IsPETase) into {self.pdb_file.parent}."
            )

        self._load_pdb()

    def _load_pdb(self) -> None:
        """Parse PDB file and index all residues."""
        if PDBParser is None:
            raise ImportError("biopython is required for structure parsing. Install via 'pip install biopython'.")

        parser = PDBParser(QUIET=True)
        self._structure = parser.get_structure(self.structure_id, str(self.pdb_file))

        for model in self._structure:
            for chain in model:
                chain_id = chain.id
                self._residues[chain_id] = {}
                for res in chain:
                    hetflag, resseq, icode = res.get_id()
                    if hetflag.strip() != "":
                        # Heteroatom / ligand / water
                        continue

                    res_name_3 = res.get_resname().strip().upper()
                    res_name_1 = protein_letters_3to1.get(res_name_3, "X")
                    is_std = res_name_1 != "X"

                    ca_coord = None
                    if "CA" in res:
                        ca_coord = tuple(res["CA"].get_coord())

                    self._residues[chain_id][resseq] = ResidueInfo(
                        chain_id=chain_id,
                        res_name_3=res_name_3,
                        res_name_1=res_name_1,
                        res_seq=resseq,
                        insertion_code=icode,
                        is_standard_aa=is_std,
                        ca_coord=ca_coord,
                    )
            # Use first model
            break

    @property
    def chain_ids(self) -> List[str]:
        """List of available polypeptide chain IDs."""
        return list(self._residues.keys())

    def get_residues_for_chain(self, chain_id: str) -> Dict[int, ResidueInfo]:
        """Return residue map for given chain."""
        if chain_id not in self._residues:
            raise KeyError(f"Chain '{chain_id}' not found. Available chains: {self.chain_ids}")
        return self._residues[chain_id]

    def get_sequence_from_structure(self, chain_id: str) -> Tuple[str, List[int]]:
        """Extract continuous amino acid sequence and residue numbering for chain.

        Returns:
            Tuple of (sequence_string, list_of_resseq_numbers).
        """
        chain_res = self.get_residues_for_chain(chain_id)
        sorted_res = sorted(chain_res.values(), key=lambda r: r.res_seq)
        seq = "".join(r.res_name_1 for r in sorted_res)
        numbers = [r.res_seq for r in sorted_res]
        return seq, numbers

    def inspect_catalytic_triad(
        self,
        chain_id: str = "A",
        expected_triad: Optional[Dict[str, int]] = None,
    ) -> Dict[str, bool]:
        """Verify the presence of canonical catalytic triad residues (e.g., Ser160, Asp206, His237 for 5XJH).

        Args:
            chain_id: Target chain ID.
            expected_triad: Dict mapping 1-letter or 3-letter AA -> resseq.
                           Default: {"S": 160, "D": 206, "H": 237}

        Returns:
            Dict mapping residue description -> boolean match status.
        """
        if expected_triad is None:
            expected_triad = {"S": 160, "D": 206, "H": 237}

        chain_res = self.get_residues_for_chain(chain_id)
        results = {}

        for aa_key, pos in expected_triad.items():
            expected_1l = protein_letters_3to1.get(aa_key.upper(), aa_key.upper())
            res = chain_res.get(pos)
            if res is None:
                results[f"{expected_1l}{pos}"] = False
            else:
                results[f"{expected_1l}{pos}"] = (res.res_name_1 == expected_1l)

        return results

    def map_mutation_to_structure(
        self,
        mutation: SingleMutation,
        chain_id: str = "A",
        offset: int = 0,
        strict: bool = True,
    ) -> Dict[str, Any]:
        """Map a SingleMutation object to PDB structure coordinates and verify wild-type identity.

        Args:
            mutation: SingleMutation instance (e.g. S160A).
            chain_id: Chain ID to map against.
            offset: Numbering offset between variant sequence numbering and PDB numbering (pdb_pos = mut_pos + offset).
            strict: If True, raises StructureMappingError on residue mismatch.

        Returns:
            Dict with structure position, wild-type residue, distance to active site (if calculable), CA coords.
        """
        chain_res = self.get_residues_for_chain(chain_id)
        pdb_pos = mutation.position + offset

        res = chain_res.get(pdb_pos)
        if res is None:
            msg = f"Residue position {pdb_pos} (mutation pos {mutation.position} + offset {offset}) not found in Chain {chain_id}."
            if strict:
                raise StructureMappingError(msg)
            return {"mapped": False, "error": msg}

        if res.res_name_1 != mutation.from_residue:
            msg = (
                f"Structure residue mismatch at chain {chain_id} pos {pdb_pos}: "
                f"structure has '{res.res_name_1}' ({res.res_name_3}), but mutation specifies '{mutation.from_residue}'"
            )
            if strict:
                raise StructureMappingError(msg)
            return {"mapped": False, "error": msg, "structure_residue": res.res_name_1}

        return {
            "mapped": True,
            "chain_id": chain_id,
            "pdb_position": pdb_pos,
            "from_residue": mutation.from_residue,
            "to_residue": mutation.to_residue,
            "ca_coord": res.ca_coord,
            "is_standard_aa": res.is_standard_aa,
        }

    def compute_distance_to_site(
        self,
        chain_id: str,
        target_pos: int,
        active_site_pos: int = 160,
    ) -> Optional[float]:
        """Calculate Euclidean CA-CA distance (in Angstroms) between a target position and active site residue."""
        chain_res = self.get_residues_for_chain(chain_id)
        res_target = chain_res.get(target_pos)
        res_active = chain_res.get(active_site_pos)

        if not res_target or not res_active:
            return None
        if not res_target.ca_coord or not res_active.ca_coord:
            return None

        p1 = np.array(res_target.ca_coord)
        p2 = np.array(res_active.ca_coord)
        return float(np.linalg.norm(p1 - p2))

    def get_active_site_shell_residues(
        self,
        chain_id: str = "A",
        catalytic_center_pos: int = 160,
        radius_angstrom: float = 8.0,
    ) -> List[ResidueInfo]:
        """Identify all residues with CA within radius of the catalytic center (e.g. Ser160).

        Args:
            chain_id: Chain ID.
            catalytic_center_pos: Position of catalytic residue (default 160 for IsPETase Ser160).
            radius_angstrom: Distance cutoff in Angstroms.

        Returns:
            List of ResidueInfo for residues within shell.
        """
        chain_res = self.get_residues_for_chain(chain_id)
        center = chain_res.get(catalytic_center_pos)
        if not center or not center.ca_coord:
            raise ValueError(f"Catalytic center position {catalytic_center_pos} not found on chain {chain_id}")

        c_coord = np.array(center.ca_coord)
        shell = []
        for res in chain_res.values():
            if res.ca_coord is not None:
                dist = np.linalg.norm(np.array(res.ca_coord) - c_coord)
                if dist <= radius_angstrom:
                    shell.append(res)

        return sorted(shell, key=lambda r: r.res_seq)
