"""Integration tests for Phase 4 Classical Chemistry Layer."""

from pathlib import Path
import tempfile
import pandas as pd
import pytest

from chemistry.config import ChemistryConfig, ClusterConfig, ElectronicStructureConfig
from chemistry.evaluate import ChemistryPipeline
from data.contracts import verify_contract


def test_phase4_end_to_end_pipeline():
    """Verifies complete Phase 4 end-to-end flow from input candidates to chem_results.parquet."""
    pdb_path = Path("data/structures/5xjh.pdb")
    if not pdb_path.exists():
        pytest.skip("5XJH structure not found.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        input_candidates_path = tmp_path / "selected_candidates.parquet"
        output_results_path = tmp_path / "chem_results.parquet"
        active_site_report_path = tmp_path / "active_site_report.json"
        clusters_dir = tmp_path / "clusters"
        manifest_path = clusters_dir / "cluster_manifest.json"
        cache_dir = tmp_path / "cache"

        # Create a small controlled candidate test dataset
        candidates_data = [
            {
                "job_id": "job_001",
                "variant_id": "VAR_WT",
                "mutations": "WT",
                "parent_enzyme": "IsPETase",
                "predicted_performance": 1.25,
                "acquisition_score": 0.95,
                "selection_rank": 1,
                "selection_reason": "High predicted fitness reference",
                "data_source": "synthetic_test_fixture",
            },
            {
                "job_id": "job_002",
                "variant_id": "VAR_S160A",
                "mutations": "S160A",
                "parent_enzyme": "IsPETase",
                "predicted_performance": 0.10,
                "acquisition_score": 0.88,
                "selection_rank": 2,
                "selection_reason": "Active-site catalytic knock-out probe",
                "data_source": "synthetic_test_fixture",
            },
            {
                "job_id": "job_003",
                "variant_id": "VAR_R280A",
                "mutations": "R280A",
                "parent_enzyme": "IsPETase",
                "predicted_performance": 1.40,
                "acquisition_score": 0.82,
                "selection_rank": 3,
                "selection_reason": "Distal surface mutation",
                "data_source": "synthetic_test_fixture",
            },
        ]
        pd.DataFrame(candidates_data).to_parquet(input_candidates_path, index=False)

        # Configure pipeline
        config = ChemistryConfig(
            cluster=ClusterConfig(
                reference_pdb_path=pdb_path,
                reference_chain_id="A",
                active_site_residues=[160, 206, 237, 87, 161, 185, 159],
            ),
            electronic_structure=ElectronicStructureConfig(
                method="HF",
                basis="sto-3g",
                charge=0,
                spin_multiplicity=1,
            ),
            cache_dir=cache_dir,
            clusters_dir=clusters_dir,
            output_results_parquet=output_results_path,
            output_active_site_report=active_site_report_path,
            output_cluster_manifest=manifest_path,
        )

        pipeline = ChemistryPipeline(config=config, test_fixture_mode=True)
        df_results = pipeline.run(candidates_parquet=input_candidates_path, run_dft=False)

        # 1. Output file assertions
        assert output_results_path.exists()
        assert active_site_report_path.exists()
        assert manifest_path.exists()
        assert len(df_results) == 3

        # 2. Structural and provenance assertions
        row_wt = df_results[df_results["variant_id"] == "VAR_WT"].iloc[0]
        row_s160a = df_results[df_results["variant_id"] == "VAR_S160A"].iloc[0]
        row_r280a = df_results[df_results["variant_id"] == "VAR_R280A"].iloc[0]

        assert row_wt["geometry_source"] == "experimental_structure"
        assert row_s160a["geometry_source"] == "model_generated_from_5XJH"
        assert row_r280a["geometry_source"] == "experimental_structure"

        # 3. Calculation & Convergence assertions
        assert bool(row_wt["scf_converged"]) is True
        assert bool(row_s160a["scf_converged"]) is True
        assert bool(row_r280a["scf_converged"]) is True
        assert row_wt["total_energy"] is not None
        assert row_s160a["total_energy"] is not None

        # 4. Relative Delta Energy assertions
        # WT delta energy should be 0.0
        assert row_wt["delta_energy"] == pytest.approx(0.0, abs=1e-5)
        # S160A delta energy should be non-null
        assert row_s160a["delta_energy"] is not None

        # 5. Synthetic quality flag assertions
        assert all(df_results["data_quality_flag"] == "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA")
        assert all(df_results["data_source"] == "synthetic_test_fixture")

        # 6. Verify cluster XYZ files generated
        xyz_files = list(clusters_dir.glob("*.xyz"))
        assert len(xyz_files) >= 3
