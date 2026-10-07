"""Unit tests for Phase 4 Classical Chemistry Layer."""

import json
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest

from chemistry.active_site import ActiveSiteExtractor, ActiveSiteReport
from chemistry.cluster import ClusterAtom, ClusterBuilder, ReducedCluster
from chemistry.config import ChemistryConfig, ClusterConfig, ElectronicStructureConfig
from chemistry.descriptors import DescriptorExtractor, MechanisticDescriptors
from chemistry.electronic_structure import (
    ElectronicStructureEngine,
    ElectronicStructureResult,
)
from chemistry.geometry import GeometryValidationResult, GeometryValidator
from chemistry.mutation import (
    MutationClusterEngine,
    MutationClusterMapping,
    VariantClusterResult,
)
from chemistry.outputs import CHEMISTRY_SCHEMA_COLUMNS, ChemistryOutputWriter
from chemistry.structure import AtomCoord, ResidueAtoms, StructureReader
from data.contracts import verify_contract


@pytest.fixture
def structure_reader():
    pdb_path = Path("data/structures/5xjh.pdb")
    if not pdb_path.exists():
        pytest.skip("5XJH structure not found.")
    return StructureReader(pdb_path=pdb_path, chain_id="A")


@pytest.fixture
def sample_cluster():
    atoms = [
        ClusterAtom(symbol="C", x=0.0, y=0.0, z=0.0, res_name="SER", res_seq=160, atom_name="CA"),
        ClusterAtom(symbol="O", x=1.2, y=0.0, z=0.0, res_name="SER", res_seq=160, atom_name="OG"),
        ClusterAtom(symbol="N", x=0.0, y=1.3, z=0.0, res_name="HIS", res_seq=237, atom_name="NE2"),
        ClusterAtom(symbol="O", x=0.0, y=0.0, z=1.4, res_name="ASP", res_seq=206, atom_name="OD1"),
    ]
    return ReducedCluster(
        cluster_id="test_cluster",
        pdb_id="5XJH",
        chain_id="A",
        parent_enzyme="IsPETase",
        residues_included=[160, 206, 237],
        atoms=atoms,
    )


def test_structure_reader_5xjh(structure_reader):
    """Verifies that PDB 5XJH loads correctly and extracts residues for Chain A."""
    assert structure_reader.chain_id == "A"
    assert structure_reader.metadata["pdb_id"] == "5XJH"
    assert len(structure_reader.residues) > 200

    # Ser160 catalytic nucleophile must be present
    ser160 = structure_reader.get_residue(160)
    assert ser160 is not None
    assert ser160.res_name == "SER"
    assert ser160.ca_atom is not None
    assert len(ser160.atoms) >= 5


def test_active_site_extractor(structure_reader):
    """Verifies detection of the 7 catalytic and binding residues in 5XJH."""
    extractor = ActiveSiteExtractor()
    residues, report = extractor.extract(structure_reader)

    assert report.mapping_status == "COMPLETE"
    assert len(report.residues_missing) == 0
    assert len(report.residues_found) == 7
    assert 160 in residues
    assert 206 in residues
    assert 237 in residues
    assert 87 in residues
    assert 161 in residues
    assert 185 in residues
    assert 159 in residues


def test_active_site_missing_residue_handling():
    """Verifies that missing residues are flagged cleanly in the active site report."""
    config = ClusterConfig(active_site_residues=[160, 9999])
    extractor = ActiveSiteExtractor(config=config)
    reader = StructureReader("data/structures/5xjh.pdb", chain_id="A")
    residues, report = extractor.extract(reader)

    assert report.mapping_status == "PARTIAL"
    assert 9999 in report.residues_missing
    assert 160 in report.residues_found


def test_reduced_cluster_building(structure_reader):
    """Verifies construction of reduced active-site cluster and XYZ export."""
    extractor = ActiveSiteExtractor()
    residues, _ = extractor.extract(structure_reader)
    builder = ClusterBuilder()
    cluster = builder.build_wildtype_cluster(residues, pdb_id="5XJH")

    assert cluster.atom_count > 50
    assert cluster.residue_count == 7
    assert cluster.center_residue == 160
    assert len(cluster.geometry_hash) == 64

    xyz_str = cluster.to_xyz_string()
    assert str(cluster.atom_count) in xyz_str.splitlines()[0]


def test_mutation_mapping_inside_and_outside(structure_reader):
    """Verifies that active-site mutations modify the cluster while distal mutations are unperturbed."""
    extractor = ActiveSiteExtractor()
    residues, _ = extractor.extract(structure_reader)
    builder = ClusterBuilder()
    wt_cluster = builder.build_wildtype_cluster(residues, pdb_id="5XJH")

    engine = MutationClusterEngine(reader=structure_reader, catalytic_center=160)

    # Mutation inside cluster: S160A
    res_inside = engine.generate_variant_cluster(
        variant_id="VAR_S160A",
        mutations_str="S160A",
        wt_cluster=wt_cluster,
    )
    assert res_inside.geometry_source == "model_generated_from_5XJH"
    assert res_inside.cluster_includes_mutation is True
    assert res_inside.mappings[0].is_inside_cluster is True
    assert res_inside.mappings[0].mutation_cluster_relation == "inside_cluster"

    # Mutation outside cluster: R280A (distal)
    res_outside = engine.generate_variant_cluster(
        variant_id="VAR_R280A",
        mutations_str="R280A",
        wt_cluster=wt_cluster,
    )
    assert res_outside.geometry_source == "experimental_structure"
    assert res_outside.cluster_includes_mutation is False
    assert res_outside.mappings[0].is_inside_cluster is False
    assert res_outside.mappings[0].mutation_cluster_relation == "outside_cluster"
    assert res_outside.mappings[0].distance_to_active_site > 10.0


def test_geometry_validation_valid_and_invalid(sample_cluster):
    """Verifies geometry validator detects steric clashes and NaN coordinates."""
    validator = GeometryValidator(min_distance_angstrom=0.50)
    res_valid = validator.validate(sample_cluster)
    assert res_valid.is_valid is True
    assert res_valid.geometry_status == "valid"

    # Steric clash cluster (<0.5 A)
    clashing_atoms = [
        ClusterAtom(symbol="C", x=0.0, y=0.0, z=0.0, res_name="SER", res_seq=160, atom_name="CA"),
        ClusterAtom(symbol="C", x=0.2, y=0.0, z=0.0, res_name="SER", res_seq=160, atom_name="CB"),
    ]
    clash_cluster = ReducedCluster(
        cluster_id="clash_cluster",
        pdb_id="5XJH",
        chain_id="A",
        parent_enzyme="IsPETase",
        residues_included=[160],
        atoms=clashing_atoms,
    )
    res_clash = validator.validate(clash_cluster)
    assert res_clash.is_valid is False
    assert res_clash.geometry_status == "invalid"
    assert any("clash" in issue.lower() for issue in res_clash.issues)


def test_electronic_structure_calculation_and_caching(sample_cluster):
    """Verifies electronic structure calculation, result fields, and cache key determinism."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = ElectronicStructureEngine(cache_dir=tmp_dir)

        # Run calculation
        res1 = engine.compute(sample_cluster, method="HF", basis="sto-3g")
        assert res1.scf_converged is True
        assert res1.total_energy is not None
        assert res1.homo_lumo_gap is not None
        assert res1.dipole_magnitude is not None
        assert res1.calculation_status == "COMPLETED"

        # Check that cache file was created
        cache_files = list(Path(tmp_dir).glob("*.json"))
        assert len(cache_files) == 1

        # Second run should load from cache
        res2 = engine.compute(sample_cluster, method="HF", basis="sto-3g")
        assert res2.calculation_key == res1.calculation_key
        assert res2.total_energy == res1.total_energy


def test_mechanistic_descriptors_and_delta_energy(sample_cluster):
    """Verifies relative delta energy extraction against wild-type baseline."""
    engine = ElectronicStructureEngine()
    elec_ref = engine.compute(sample_cluster, method="HF", basis="sto-3g")

    # Mutant cluster with slightly perturbed coordinate
    mut_atoms = [
        ClusterAtom(symbol="C", x=0.0, y=0.0, z=0.0, res_name="ALA", res_seq=160, atom_name="CA"),
        ClusterAtom(symbol="C", x=1.3, y=0.0, z=0.0, res_name="ALA", res_seq=160, atom_name="CB"),
        ClusterAtom(symbol="N", x=0.0, y=1.3, z=0.0, res_name="HIS", res_seq=237, atom_name="NE2"),
        ClusterAtom(symbol="O", x=0.0, y=0.0, z=1.4, res_name="ASP", res_seq=206, atom_name="OD1"),
    ]
    mut_cluster = ReducedCluster(
        cluster_id="mut_cluster",
        pdb_id="5XJH",
        chain_id="A",
        parent_enzyme="IsPETase",
        residues_included=[160, 206, 237],
        atoms=mut_atoms,
    )
    elec_mut = engine.compute(mut_cluster, method="HF", basis="sto-3g")

    var_result = VariantClusterResult(
        variant_id="VAR_S160A",
        mutations="S160A",
        cluster=mut_cluster,
        geometry_source="model_generated_from_5XJH",
        mappings=[],
        cluster_includes_mutation=True,
        mutation_distances={"S160A": 0.0},
    )

    extractor = DescriptorExtractor()
    desc = extractor.extract(
        var_cluster_result=var_result,
        elec_result=elec_mut,
        ref_elec_result=elec_ref,
    )

    assert desc.variant_id == "VAR_S160A"
    assert desc.total_energy is not None
    assert desc.reference_energy == elec_ref.total_energy
    assert desc.delta_energy == pytest.approx(elec_mut.total_energy - elec_ref.total_energy, abs=1e-5)
    assert desc.geometry_source == "model_generated_from_5XJH"


def test_chemistry_outputs_parquet_and_manifest(sample_cluster):
    """Verifies creation of chem_results.parquet and cluster_manifest.json."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        clusters_dir = tmp_path / "clusters"
        out_parquet = tmp_path / "chem_results.parquet"
        manifest_json = clusters_dir / "cluster_manifest.json"

        writer = ChemistryOutputWriter(clusters_dir=clusters_dir)
        writer.write_cluster_manifest([sample_cluster], manifest_json)
        assert manifest_json.exists()

        with open(manifest_json, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            assert manifest_data["cluster_count"] == 1
            assert manifest_data["clusters"][0]["cluster_id"] == "test_cluster"

        # Mock descriptor
        desc = MechanisticDescriptors(
            variant_id="VAR_001",
            total_energy=-120.45,
            reference_energy=-120.40,
            delta_energy=-0.05,
            dipole_x=0.1,
            dipole_y=0.2,
            dipole_z=0.3,
            dipole_magnitude=0.374,
            homo_energy=-0.35,
            lumo_energy=0.05,
            homo_lumo_gap=0.40,
            catalytic_triad_ser_his_dist=2.8,
            catalytic_triad_his_asp_dist=2.7,
            min_mutation_distance_to_active_site=0.0,
            cluster_atom_count=4,
            cluster_residue_count=3,
            geometry_source="model_generated_from_5XJH",
            geometry_status="valid",
            scf_converged=True,
            scf_iterations=10,
            runtime_seconds=0.12,
            calculation_status="COMPLETED",
            failure_reason=None,
            method="HF",
            basis="sto-3g",
            charge=0,
            multiplicity=1,
        )

        df = writer.build_results_dataframe(
            descriptors_list=[desc],
            var_cluster_results={},
            data_source="synthetic_test_fixture",
            data_quality_flag="SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA",
        )

        for col in CHEMISTRY_SCHEMA_COLUMNS:
            assert col in df.columns

        writer.save_results_parquet(df, out_parquet)
        assert out_parquet.exists()

        df_loaded = pd.read_parquet(out_parquet)
        assert len(df_loaded) == 1
        assert df_loaded.iloc[0]["variant_id"] == "VAR_001"
        assert df_loaded.iloc[0]["data_quality_flag"] == "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"
