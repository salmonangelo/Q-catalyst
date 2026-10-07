"""Unit tests for structure loading, residue inspection, and mutation mapping."""

from pathlib import Path
import pytest
from data.mutations import SingleMutation
from data.structure_utils import StructureManager, StructureMappingError


@pytest.fixture
def structure_5xjh():
    pdb_path = Path("data/structures/5xjh.pdb")
    if not pdb_path.exists():
        pytest.skip("PDB 5XJH not downloaded; skipping live structure tests.")
    return StructureManager(pdb_path)


def test_structure_loading_and_chains(structure_5xjh):
    assert "A" in structure_5xjh.chain_ids
    residues_a = structure_5xjh.get_residues_for_chain("A")
    assert len(residues_a) > 200


def test_catalytic_triad_inspection(structure_5xjh):
    # In 5XJH: Ser160, Asp206, His237 form catalytic triad
    triad_status = structure_5xjh.inspect_catalytic_triad(
        chain_id="A",
        expected_triad={"S": 160, "D": 206, "H": 237}
    )
    assert triad_status.get("S160") is True
    assert triad_status.get("D206") is True
    assert triad_status.get("H237") is True


def test_map_mutation_to_structure(structure_5xjh):
    mut = SingleMutation(position=160, from_residue="S", to_residue="A")
    mapping = structure_5xjh.map_mutation_to_structure(mut, chain_id="A", offset=0)
    assert mapping["mapped"] is True
    assert mapping["pdb_position"] == 160
    assert mapping["from_residue"] == "S"
    assert mapping["to_residue"] == "A"
    assert mapping["ca_coord"] is not None


def test_map_mutation_mismatch_error(structure_5xjh):
    # Position 160 is Serine, but we assert it is Alanine -> should raise StructureMappingError
    mut = SingleMutation(position=160, from_residue="A", to_residue="G")
    with pytest.raises(StructureMappingError):
        structure_5xjh.map_mutation_to_structure(mut, chain_id="A", strict=True)


def test_compute_distance_and_active_shell(structure_5xjh):
    # Distance from Ser160 to Asp206
    dist = structure_5xjh.compute_distance_to_site(chain_id="A", target_pos=206, active_site_pos=160)
    assert dist is not None
    assert 4.0 < dist < 12.0  # reasonable catalytic pocket distance

    # Active site shell residues within 8 Angstroms of Ser160
    shell = structure_5xjh.get_active_site_shell_residues(chain_id="A", catalytic_center_pos=160, radius_angstrom=8.0)
    assert len(shell) > 0
    # Ser160 itself should be in the shell (dist = 0)
    shell_resseqs = [r.res_seq for r in shell]
    assert 160 in shell_resseqs
