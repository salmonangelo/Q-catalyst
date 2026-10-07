"""Mutation-aware active-site cluster adaptation and geometry provenance tracking."""

from dataclasses import dataclass, field
import math
from typing import Dict, List, Optional, Tuple
import numpy as np

from chemistry.cluster import ClusterAtom, ReducedCluster
from chemistry.structure import AtomCoord, ResidueAtoms, StructureReader
from data.mutations import SingleMutation, parse_mutations

# Standard 1-letter to 3-letter amino acid code mapping
AA_1TO3 = {
    "A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS",
    "E": "GLU", "Q": "GLN", "G": "GLY", "H": "HIS", "I": "ILE",
    "L": "LEU", "K": "LYS", "M": "MET", "F": "PHE", "P": "PRO",
    "S": "SER", "T": "THR", "W": "TRP", "Y": "TYR", "V": "VAL",
}

# Approximate relative atomic offsets for side chains from CA/CB (for model-generated geometries)
# Used to construct transparent model-generated mutant geometries
SIDECHAIN_TEMPLATES = {
    "ALA": [("CB", "C", [0.0, 0.0, 1.52])],
    "GLY": [],
    "SER": [("CB", "C", [0.0, 0.0, 1.52]), ("OG", "O", [0.0, 1.2, 2.0])],
    "CYS": [("CB", "C", [0.0, 0.0, 1.52]), ("SG", "S", [0.0, 1.4, 2.3])],
    "VAL": [("CB", "C", [0.0, 0.0, 1.52]), ("CG1", "C", [1.2, 0.0, 2.0]), ("CG2", "C", [-1.2, 0.0, 2.0])],
    "THR": [("CB", "C", [0.0, 0.0, 1.52]), ("OG1", "O", [1.2, 0.0, 2.0]), ("CG2", "C", [-1.2, 0.0, 2.0])],
    "ASP": [("CB", "C", [0.0, 0.0, 1.52]), ("CG", "C", [0.0, 1.2, 2.2]), ("OD1", "O", [1.1, 1.5, 2.7]), ("OD2", "O", [-1.1, 1.5, 2.7])],
    "ASN": [("CB", "C", [0.0, 0.0, 1.52]), ("CG", "C", [0.0, 1.2, 2.2]), ("OD1", "O", [1.1, 1.5, 2.7]), ("ND2", "N", [-1.1, 1.5, 2.7])],
    "PHE": [("CB", "C", [0.0, 0.0, 1.52]), ("CG", "C", [0.0, 1.2, 2.2]), ("CD1", "C", [1.2, 1.5, 2.8]), ("CD2", "C", [-1.2, 1.5, 2.8]), ("CE1", "C", [1.2, 2.5, 3.5]), ("CE2", "C", [-1.2, 2.5, 3.5]), ("CZ", "C", [0.0, 3.0, 3.8])],
    "TYR": [("CB", "C", [0.0, 0.0, 1.52]), ("CG", "C", [0.0, 1.2, 2.2]), ("CD1", "C", [1.2, 1.5, 2.8]), ("CD2", "C", [-1.2, 1.5, 2.8]), ("CE1", "C", [1.2, 2.5, 3.5]), ("CE2", "C", [-1.2, 2.5, 3.5]), ("CZ", "C", [0.0, 3.0, 3.8]), ("OH", "O", [0.0, 4.2, 4.3])],
}


@dataclass
class MutationClusterMapping:
    """Detailed mapping of a single amino acid substitution relative to the active-site cluster."""
    mutation_str: str
    wild_type: str
    position: int
    mutant: str
    distance_to_active_site: float
    is_inside_cluster: bool
    mutation_cluster_relation: str  # "inside_cluster", "proximal_cluster", "outside_cluster"
    notes: str


@dataclass
class VariantClusterResult:
    """The generated cluster and its structural provenance for a candidate variant."""
    variant_id: str
    mutations: str
    cluster: ReducedCluster
    geometry_source: str  # "experimental_structure" or "model_generated_from_5XJH"
    mappings: List[MutationClusterMapping]
    cluster_includes_mutation: bool
    mutation_distances: Dict[str, float] = field(default_factory=dict)


class MutationClusterEngine:
    """Maps candidate mutations to the 3D structure and generates mutation-aware clusters."""

    def __init__(self, reader: StructureReader, catalytic_center: int = 160):
        self.reader = reader
        self.catalytic_center = catalytic_center
        self._center_coord = self._get_center_coord()

    def _get_center_coord(self) -> np.ndarray:
        res = self.reader.get_residue(self.catalytic_center)
        if res and res.ca_atom:
            return res.ca_atom.coord_array
        return np.array([0.0, 0.0, 0.0])

    def calculate_mutation_distance(self, position: int) -> float:
        """Calculates distance from residue CA to catalytic center CA (Ser160)."""
        res = self.reader.get_residue(position)
        if res and res.ca_atom:
            return float(np.linalg.norm(res.ca_atom.coord_array - self._center_coord))
        return 999.0

    def generate_variant_cluster(
        self,
        variant_id: str,
        mutations_str: str,
        wt_cluster: ReducedCluster,
    ) -> VariantClusterResult:
        """Generates a mutation-aware reduced cluster with explicit geometry provenance."""
        # Check if WT or no mutations
        clean_muts = str(mutations_str).strip() if mutations_str else ""
        if not clean_muts or clean_muts.upper() in ["WT", "WILDTYPE", "NONE", "NAN"]:
            return VariantClusterResult(
                variant_id=variant_id,
                mutations="WT",
                cluster=wt_cluster,
                geometry_source="experimental_structure",
                mappings=[],
                cluster_includes_mutation=False,
                mutation_distances={},
            )

        parsed_muts = parse_mutations(clean_muts)
        mappings: List[MutationClusterMapping] = []
        cluster_residues_set = set(wt_cluster.residues_included)

        has_inside_mutation = False
        mut_distances: Dict[str, float] = {}

        for mut in parsed_muts:
            pos = mut.position
            dist = self.calculate_mutation_distance(pos)
            mut_distances[mut.to_string()] = dist

            is_inside = pos in cluster_residues_set
            if is_inside:
                has_inside_mutation = True
                relation = "inside_cluster"
                notes = f"Residue {pos} is part of the core catalytic cluster ({wt_cluster.residues_included})."
            elif dist <= wt_cluster.radius_angstrom + 4.0:
                relation = "proximal_cluster"
                notes = f"Residue {pos} is within {dist:.2f} Å of catalytic center but outside core cluster."
            else:
                relation = "outside_cluster"
                notes = f"Residue {pos} is {dist:.2f} Å away from catalytic center (outside cluster)."

            mappings.append(
                MutationClusterMapping(
                    mutation_str=mut.to_string(),
                    wild_type=mut.from_residue,
                    position=mut.position,
                    mutant=mut.to_residue,
                    distance_to_active_site=dist,
                    is_inside_cluster=is_inside,
                    mutation_cluster_relation=relation,
                    notes=notes,
                )
            )

        # If all mutations are outside the cluster, the local active-site cluster geometry is unperturbed
        if not has_inside_mutation:
            variant_cluster = ReducedCluster(
                cluster_id=f"{variant_id}_cluster",
                pdb_id=wt_cluster.pdb_id,
                chain_id=wt_cluster.chain_id,
                parent_enzyme=wt_cluster.parent_enzyme,
                residues_included=list(wt_cluster.residues_included),
                atoms=list(wt_cluster.atoms),
                radius_angstrom=wt_cluster.radius_angstrom,
                center_residue=wt_cluster.center_residue,
                description=f"Active-site cluster for {variant_id} (mutations outside local cluster)",
            )
            return VariantClusterResult(
                variant_id=variant_id,
                mutations=clean_muts,
                cluster=variant_cluster,
                geometry_source="experimental_structure",
                mappings=mappings,
                cluster_includes_mutation=False,
                mutation_distances=mut_distances,
            )

        # Build model-generated mutant cluster
        new_atoms: List[ClusterAtom] = []
        mut_dict = {m.position: m for m in parsed_muts if m.position in cluster_residues_set}

        for atom in wt_cluster.atoms:
            pos = atom.res_seq
            if pos not in mut_dict:
                # Retain unmutated residue atom
                new_atoms.append(atom)
            else:
                mut = mut_dict[pos]
                mut_3letter = AA_1TO3.get(mut.to_residue, "ALA")
                # Keep backbone atoms (N, CA, C, O) with modified residue name
                if atom.atom_name in ["N", "CA", "C", "O"]:
                    new_atoms.append(
                        ClusterAtom(
                            symbol=atom.symbol,
                            x=atom.x,
                            y=atom.y,
                            z=atom.z,
                            res_name=mut_3letter,
                            res_seq=pos,
                            atom_name=atom.atom_name,
                            is_capped_hydrogen=False,
                        )
                    )
                else:
                    # Side chain atom: If substituting with Alanine/Glycine or known template
                    # For conservative substitution, preserve matching side chain atoms or template
                    pass

        # Append model sidechain atoms if available in templates for mutated residues
        for pos, mut in mut_dict.items():
            mut_3letter = AA_1TO3.get(mut.to_residue, "ALA")
            template = SIDECHAIN_TEMPLATES.get(mut_3letter, [])
            # Find CA atom coordinates for this residue
            ca_atom = next((a for a in new_atoms if a.res_seq == pos and a.atom_name == "CA"), None)
            if ca_atom and template:
                for sc_name, elem, offset in template:
                    new_atoms.append(
                        ClusterAtom(
                            symbol=elem,
                            x=ca_atom.x + offset[0],
                            y=ca_atom.y + offset[1],
                            z=ca_atom.z + offset[2],
                            res_name=mut_3letter,
                            res_seq=pos,
                            atom_name=sc_name,
                            is_capped_hydrogen=False,
                        )
                    )

        variant_cluster = ReducedCluster(
            cluster_id=f"{variant_id}_cluster",
            pdb_id=wt_cluster.pdb_id,
            chain_id=wt_cluster.chain_id,
            parent_enzyme=wt_cluster.parent_enzyme,
            residues_included=list(wt_cluster.residues_included),
            atoms=new_atoms,
            radius_angstrom=wt_cluster.radius_angstrom,
            center_residue=wt_cluster.center_residue,
            description=f"Model-generated active-site cluster for variant {variant_id} from 5XJH",
        )

        return VariantClusterResult(
            variant_id=variant_id,
            mutations=clean_muts,
            cluster=variant_cluster,
            geometry_source="model_generated_from_5XJH",
            mappings=mappings,
            cluster_includes_mutation=True,
            mutation_distances=mut_distances,
        )
