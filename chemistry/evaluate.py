"""CLI and pipeline orchestrator for Phase 4 Classical Chemistry Layer."""

import argparse
import logging
from pathlib import Path
import sys
from typing import Dict, List, Optional
import pandas as pd

from chemistry.active_site import ActiveSiteExtractor
from chemistry.cluster import ClusterBuilder, ReducedCluster
from chemistry.config import ChemistryConfig, ClusterConfig, ElectronicStructureConfig
from chemistry.descriptors import DescriptorExtractor, MechanisticDescriptors
from chemistry.electronic_structure import ElectronicStructureEngine, ElectronicStructureResult
from chemistry.mutation import MutationClusterEngine, VariantClusterResult
from chemistry.outputs import ChemistryOutputWriter
from chemistry.structure import StructureReader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("QCatalyst-Chemistry")


class ChemistryPipeline:
    """Executes the classical chemistry evaluation workflow on selected candidates."""

    def __init__(self, config: Optional[ChemistryConfig] = None, test_fixture_mode: bool = False):
        self.config = config or ChemistryConfig()
        self.test_fixture_mode = test_fixture_mode
        self.reader = StructureReader(
            pdb_path=self.config.cluster.reference_pdb_path,
            chain_id=self.config.cluster.reference_chain_id,
        )
        self.active_site_extractor = ActiveSiteExtractor(self.config.cluster)
        self.cluster_builder = ClusterBuilder(self.config.cluster)
        self.mutation_engine = MutationClusterEngine(
            reader=self.reader,
            catalytic_center=self.config.cluster.catalytic_center_residue,
        )
        self.elec_engine = ElectronicStructureEngine(
            config=self.config.electronic_structure,
            cache_dir=self.config.cache_dir,
        )
        self.descriptor_extractor = DescriptorExtractor()
        self.output_writer = ChemistryOutputWriter(self.config.clusters_dir)

    def validate_input(self, df: pd.DataFrame) -> None:
        """Validates that input DataFrame satisfies the Phase 3 acquisition contract."""
        required_cols = ["variant_id", "mutations"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Input candidates missing required columns: {missing}")

        # Check if synthetic fixture is being run without explicit flag
        if "data_source" in df.columns:
            sources = set(df["data_source"].dropna().unique())
            if any("synthetic" in s.lower() for s in sources) and not self.test_fixture_mode:
                raise ValueError(
                    "Input contains synthetic fixtures. To run chemistry pipeline on test fixtures, "
                    "you must explicitly pass the --test-fixture flag."
                )

    def run(
        self,
        candidates_parquet: Path | str = "acquisition/selected_candidates.parquet",
        run_dft: bool = False,
    ) -> pd.DataFrame:
        """Runs the complete classical chemistry layer pipeline."""
        input_path = Path(candidates_parquet)
        if not input_path.exists():
            raise FileNotFoundError(
                f"Selected candidates input not found: {input_path}. "
                f"Please ensure Phase 3 acquisition has executed or provide an input file."
            )

        logger.info(f"Loading selected candidates from: {input_path}")
        df_candidates = pd.read_parquet(input_path)
        self.validate_input(df_candidates)
        logger.info(f"Loaded {len(df_candidates)} candidates for chemistry triage.")

        # Step 1: Active-site extraction & reporting
        logger.info("Extracting and verifying active-site catalytic residues from 5XJH...")
        active_site_residues, report = self.active_site_extractor.extract(self.reader)
        report.save_json(self.config.output_active_site_report)
        logger.info(
            f"Active site mapping: {report.mapping_status} "
            f"({len(report.residues_found)}/{len(report.residues_requested)} residues, {report.atom_count} atoms)."
        )

        # Step 2: Build Wild-Type reference cluster
        wt_cluster = self.cluster_builder.build_wildtype_cluster(
            active_site_residues=active_site_residues,
            pdb_id=self.reader.metadata.get("pdb_id", "5XJH"),
            cluster_id="WT_5XJH_active_site",
        )
        self.output_writer.export_cluster_xyz(wt_cluster, "WT_cluster.xyz")

        # Step 3: Compute Wild-Type reference electronic structure
        method_to_use = "DFT" if run_dft else self.config.electronic_structure.method
        basis_to_use = self.config.electronic_structure.dft_basis if run_dft else self.config.electronic_structure.basis

        logger.info(f"Computing WT reference electronic structure ({method_to_use}/{basis_to_use})...")
        ref_elec_result = self.elec_engine.compute(
            cluster=wt_cluster,
            method=method_to_use,
            basis=basis_to_use,
        )
        logger.info(
            f"WT Reference converged: {ref_elec_result.scf_converged}, "
            f"Energy: {ref_elec_result.total_energy:.6f} Ha" if ref_elec_result.total_energy is not None else "WT calculation error"
        )

        # Step 4: Process Candidates
        all_clusters: List[ReducedCluster] = [wt_cluster]
        all_descriptors: List[MechanisticDescriptors] = []
        var_cluster_results: Dict[str, VariantClusterResult] = {}

        for _, row in df_candidates.iterrows():
            var_id = str(row["variant_id"])
            muts = str(row.get("mutations", "WT"))

            logger.info(f"Processing candidate: {var_id} ({muts})")

            # Build variant cluster
            v_res = self.mutation_engine.generate_variant_cluster(
                variant_id=var_id,
                mutations_str=muts,
                wt_cluster=wt_cluster,
            )
            var_cluster_results[var_id] = v_res
            all_clusters.append(v_res.cluster)

            # Export individual XYZ
            self.output_writer.export_cluster_xyz(v_res.cluster, f"{var_id}_cluster.xyz")

            # Run electronic structure calculation
            elec_res = self.elec_engine.compute(
                cluster=v_res.cluster,
                method=method_to_use,
                basis=basis_to_use,
            )

            # Extract descriptors
            desc = self.descriptor_extractor.extract(
                var_cluster_result=v_res,
                elec_result=elec_res,
                ref_elec_result=ref_elec_result,
            )
            all_descriptors.append(desc)

        # Step 5: Export Manifest and Results
        logger.info("Writing cluster manifest and chem_results.parquet...")
        self.output_writer.write_cluster_manifest(all_clusters, self.config.output_cluster_manifest)

        data_source = "synthetic_test_fixture" if self.test_fixture_mode else "IsPETase_5XJH_Structure"
        data_quality_flag = (
            "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"
            if self.test_fixture_mode
            else "COMPUTED_CLASSICAL_ELECTRONIC_STRUCTURE"
        )

        df_results = self.output_writer.build_results_dataframe(
            descriptors_list=all_descriptors,
            var_cluster_results=var_cluster_results,
            data_source=data_source,
            data_quality_flag=data_quality_flag,
        )

        self.output_writer.save_results_parquet(df_results, self.config.output_results_parquet)
        logger.info(f"Phase 4 chemistry evaluation complete! Saved {len(df_results)} results to {self.config.output_results_parquet}")
        return df_results


def main():
    parser = argparse.ArgumentParser(description="Phase 4 Classical Chemistry Layer Evaluation")
    parser.add_argument("--input", type=str, default="acquisition/selected_candidates.parquet", help="Path to input candidates parquet")
    parser.add_argument("--output", type=str, default="chemistry/chem_results.parquet", help="Path to output chemistry parquet")
    parser.add_argument("--run-dft", action="store_true", help="Execute DFT calculations in addition to HF baseline")
    parser.add_argument("--test-fixture", action="store_true", help="Explicit flag when executing on synthetic test fixtures")
    args = parser.parse_args()

    config = ChemistryConfig()
    if args.output:
        config.output_results_parquet = Path(args.output)

    pipeline = ChemistryPipeline(config=config, test_fixture_mode=args.test_fixture)
    pipeline.run(candidates_parquet=args.input, run_dft=args.run_dft)


if __name__ == "__main__":
    main()
