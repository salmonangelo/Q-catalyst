"""Active-site extraction, verification, and reporting for PETase structures."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Dict, List, Optional

from chemistry.config import ClusterConfig
from chemistry.structure import AtomCoord, ResidueAtoms, StructureReader


# Expected amino acid 3-letter codes for IsPETase 5XJH active site residues
EXPECTED_ACTIVE_SITE_RESIDUES = {
    160: "SER",  # Catalytic nucleophile
    206: "ASP",  # Catalytic acid/base
    237: "HIS",  # Catalytic base
    87: "TYR",   # Oxyanion hole
    161: "MET",  # Oxyanion hole / subsite
    185: "TRP",  # Substrate-binding / aromatic cleft
    159: "TRP",  # Substrate-binding / aromatic cleft
}


@dataclass
class ResidueSummary:
    res_seq: int
    res_name: str
    expected_name: str
    is_match: bool
    atom_count: int
    ca_coord: Optional[List[float]] = None


@dataclass
class ActiveSiteReport:
    pdb_id: str
    chain: str
    structure_file: str
    residues_requested: List[int]
    residues_found: List[int]
    residues_missing: List[int]
    atom_count: int
    mapping_status: str  # "COMPLETE", "PARTIAL", "FAILED"
    residue_details: List[ResidueSummary] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    def save_json(self, output_path: Path | str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class ActiveSiteExtractor:
    """Extracts and verifies the configured active-site catalytic region from PDB structures."""

    def __init__(self, config: Optional[ClusterConfig] = None):
        self.config = config or ClusterConfig()

    def extract(self, reader: Optional[StructureReader] = None) -> tuple[Dict[int, ResidueAtoms], ActiveSiteReport]:
        """Loads and verifies active site residues from the structure reader."""
        if reader is None:
            reader = StructureReader(
                pdb_path=self.config.reference_pdb_path,
                chain_id=self.config.reference_chain_id,
            )

        requested = self.config.active_site_residues
        found_residues: Dict[int, ResidueAtoms] = {}
        found_seqs: List[int] = []
        missing_seqs: List[int] = []
        details: List[ResidueSummary] = []
        total_atoms = 0

        for seq in requested:
            res = reader.get_residue(seq)
            expected_name = EXPECTED_ACTIVE_SITE_RESIDUES.get(seq, "")
            if res is not None:
                found_residues[seq] = res
                found_seqs.append(seq)
                total_atoms += len(res.atoms)
                ca = res.ca_atom
                ca_coord = ca.coord_array.tolist() if ca else None
                is_match = (res.res_name == expected_name) if expected_name else True
                details.append(
                    ResidueSummary(
                        res_seq=seq,
                        res_name=res.res_name,
                        expected_name=expected_name,
                        is_match=is_match,
                        atom_count=len(res.atoms),
                        ca_coord=ca_coord,
                    )
                )
            else:
                missing_seqs.append(seq)
                details.append(
                    ResidueSummary(
                        res_seq=seq,
                        res_name="MISSING",
                        expected_name=expected_name,
                        is_match=False,
                        atom_count=0,
                        ca_coord=None,
                    )
                )

        if not missing_seqs:
            status = "COMPLETE"
        elif len(found_seqs) > 0:
            status = "PARTIAL"
        else:
            status = "FAILED"

        report = ActiveSiteReport(
            pdb_id=reader.metadata.get("pdb_id", "5XJH"),
            chain=reader.chain_id,
            structure_file=reader.metadata.get("structure_file", str(self.config.reference_pdb_path)),
            residues_requested=requested,
            residues_found=found_seqs,
            residues_missing=missing_seqs,
            atom_count=total_atoms,
            mapping_status=status,
            residue_details=details,
        )

        return found_residues, report
