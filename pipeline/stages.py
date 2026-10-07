"""Stage definitions and adapters for end-to-end pipeline execution."""

import abc
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import pandas as pd

from pipeline.config import PipelineConfig
from pipeline.context import PipelineContext, StageStatus

logger = logging.getLogger("QCatalyst-Pipeline")


class PipelineStage(abc.ABC):
    """Abstract base class for an orchestrable pipeline stage."""

    def __init__(self, name: str, optional: bool = False):
        self.name = name
        self.optional = optional

    @abc.abstractmethod
    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        """Executes stage logic and returns True if successful."""
        pass


class DataStage(PipelineStage):
    """Stage 1: Validates curated variant dataset and discovers candidate batch."""

    def __init__(self):
        super().__init__(name="data", optional=False)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        var_path = config.variants_parquet
        if var_path.exists():
            df_var = pd.read_parquet(var_path)
            if df_var.empty:
                context.record_stage_failure(self.name, 0.0, "Curated variants dataset is empty.")
                return False

            # Check synthetic data flags
            is_synthetic = False
            data_quality_flag = "VERIFIED_DATA"
            data_source = "curated_variants"
            if "data_quality_flag" in df_var.columns:
                flags = df_var["data_quality_flag"].astype(str).unique()
                if any("SYNTHETIC" in f.upper() for f in flags):
                    is_synthetic = True
                    data_quality_flag = "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"
                    data_source = "synthetic_test_fixture"

            context.synthetic_data_present = is_synthetic
            context.data_quality_flag = data_quality_flag
            context.data_source = data_source

            all_cids = df_var["variant_id"].astype(str).tolist()
            if config.candidate_limit and len(all_cids) > config.candidate_limit:
                selected_cids = all_cids[: config.candidate_limit]
                context.add_warning(f"Truncated candidate list from {len(all_cids)} to {config.candidate_limit}.")
            else:
                selected_cids = all_cids

            context.candidate_count = len(selected_cids)
            context.candidate_ids = selected_cids
            context.candidate_selection_policy = config.candidate_selection_policy
            context.input_artifacts["variants_parquet"] = str(var_path)
            return True

        # If variants parquet not present, check raw data
        raw_dir = Path("data/raw")
        if raw_dir.exists() and any(raw_dir.glob("*.csv")):
            from data.build_dataset import build_curated_dataset
            logger.info("Building curated dataset from raw benchmarks...")
            df_built, _ = build_curated_dataset()
            all_cids = df_built["variant_id"].astype(str).tolist()
            context.candidate_count = len(all_cids)
            context.candidate_ids = all_cids
            context.input_artifacts["variants_parquet"] = str(var_path)
            return True

        # If raw data also absent, check existing downstream parquet artifacts
        downstream_paths = [
            config.fusion_results_parquet,
            config.quantum_parquet,
            config.chemistry_parquet,
            config.acquisition_parquet,
            config.protein_ai_parquet,
        ]
        discovered_cids = set()
        for p in downstream_paths:
            if p.exists():
                try:
                    df_p = pd.read_parquet(p)
                    for col in ["candidate_id", "variant_id", "job_id"]:
                        if col in df_p.columns:
                            discovered_cids.update(df_p[col].dropna().astype(str).tolist())
                except Exception:
                    pass

        if discovered_cids:
            cids_sorted = sorted(list(discovered_cids))
            if config.candidate_limit and len(cids_sorted) > config.candidate_limit:
                cids_sorted = cids_sorted[: config.candidate_limit]

            context.candidate_count = len(cids_sorted)
            context.candidate_ids = cids_sorted
            context.data_source = "discovered_downstream_artifacts"
            context.data_quality_flag = "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA" if context.synthetic_data_present else "INFERRED_CANDIDATES"
            context.input_artifacts["data_source_note"] = "Curated dataset absent; candidates discovered from available downstream artifacts."
            logger.info(f"Discovered {len(cids_sorted)} candidate(s) from downstream artifacts: {cids_sorted}")
            return True

        context.record_stage_failure(
            self.name,
            duration_sec=0.0,
            error_msg=f"Curated variants dataset not found at {var_path} and no benchmark data present in data/raw/",
        )
        return False


class ProteinAIStage(PipelineStage):
    """Stage 2: Runs sequence-based fitness representation and inference."""

    def __init__(self):
        super().__init__(name="protein_ai", optional=False)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        pred_path = config.protein_ai_parquet
        if config.reuse_cached_outputs and pred_path.exists():
            context.output_artifacts["protein_ai_parquet"] = str(pred_path)
            return True

        from protein_ai.inference import run_protein_ai_pipeline
        run_protein_ai_pipeline(
            variants_parquet=config.variants_parquet,
            output_predictions_path=pred_path,
            split_strategy=config.split_strategy,
        )

        if not pred_path.exists():
            context.record_stage_failure(self.name, 0.0, f"Expected output {pred_path} was not created.")
            return False

        context.output_artifacts["protein_ai_parquet"] = str(pred_path)
        return True


class UncertaintyStage(PipelineStage):
    """Stage 3: Computes ensemble, OOD, and conformal uncertainty estimates."""

    def __init__(self):
        super().__init__(name="uncertainty", optional=False)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        unc_path = config.uncertainty_parquet
        g0_path = config.gate0_report_json
        if config.reuse_cached_outputs and unc_path.exists() and g0_path.exists():
            context.output_artifacts["uncertainty_parquet"] = str(unc_path)
            context.output_artifacts["gate0_report_json"] = str(g0_path)
            return True

        from uncertainty.evaluate import run_uncertainty_evaluation
        run_uncertainty_evaluation(
            variants_parquet=config.variants_parquet,
            predictions_parquet=config.protein_ai_parquet,
            output_uncertainty_path=unc_path,
            gate0_json_path=g0_path,
            split_strategy=config.split_strategy,
        )

        if not unc_path.exists():
            context.record_stage_failure(self.name, 0.0, f"Expected output {unc_path} was not created.")
            return False

        context.output_artifacts["uncertainty_parquet"] = str(unc_path)
        context.output_artifacts["gate0_report_json"] = str(g0_path)
        return True


class AcquisitionStage(PipelineStage):
    """Stage 4: Executes mechanism-aware acquisition gating and candidate budget selection."""

    def __init__(self):
        super().__init__(name="acquisition", optional=False)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        acq_path = config.acquisition_parquet
        jobs_path = config.chem_jobs_json
        if config.reuse_cached_outputs and acq_path.exists() and jobs_path.exists():
            context.output_artifacts["acquisition_parquet"] = str(acq_path)
            context.output_artifacts["chem_jobs_json"] = str(jobs_path)
            return True

        from acquisition.evaluate import run_acquisition_pipeline
        run_acquisition_pipeline(
            predictions_parquet=config.protein_ai_parquet,
            uncertainty_parquet=config.uncertainty_parquet,
            variants_parquet=config.variants_parquet,
            gate0_json_path=config.gate0_report_json,
            output_jobs_json=jobs_path,
            output_candidates_parquet=acq_path,
            is_synthetic_run=context.synthetic_data_present,
        )

        if not acq_path.exists():
            context.record_stage_failure(self.name, 0.0, f"Expected output {acq_path} was not created.")
            return False

        context.output_artifacts["acquisition_parquet"] = str(acq_path)
        context.output_artifacts["chem_jobs_json"] = str(jobs_path)
        return True


class ChemistryStage(PipelineStage):
    """Stage 5: Runs classical cluster extraction, geometry validation, and HF electronic structure."""

    def __init__(self):
        super().__init__(name="chemistry", optional=False)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        chem_path = config.chemistry_parquet
        manifest_path = config.cluster_manifest_json
        if config.reuse_cached_outputs and chem_path.exists() and manifest_path.exists():
            context.output_artifacts["chemistry_parquet"] = str(chem_path)
            context.output_artifacts["cluster_manifest_json"] = str(manifest_path)
            return True

        from chemistry.evaluate import ChemistryPipeline
        chem_pipeline = ChemistryPipeline(test_fixture_mode=context.synthetic_data_present)
        chem_pipeline.run(candidates_parquet=config.acquisition_parquet)

        if not chem_path.exists():
            context.record_stage_failure(self.name, 0.0, f"Expected output {chem_path} was not created.")
            return False

        context.output_artifacts["chemistry_parquet"] = str(chem_path)
        context.output_artifacts["cluster_manifest_json"] = str(manifest_path)
        return True


class QuantumStage(PipelineStage):
    """Stage 6: Executes active-space (4e, 4o) VQE quantum simulation with exact CASCI verification."""

    def __init__(self):
        super().__init__(name="quantum", optional=True)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        qm_path = config.quantum_parquet
        manifest_path = config.quantum_manifest_json
        
        # Check caching
        if config.reuse_cached_outputs and qm_path.exists() and manifest_path.exists():
            context.output_artifacts["quantum_parquet"] = str(qm_path)
            context.output_artifacts["quantum_manifest_json"] = str(manifest_path)
            context.quantum_backend_type = "SIMULATOR"
            context.integral_backend = "CLASSICAL_FALLBACK"
            
            # Read simulated variants from existing table
            try:
                df_qm = pd.read_parquet(qm_path)
                sim_cids = df_qm["variant_id"].astype(str).tolist()
                context.quantum_candidates_processed = sim_cids
                context.quantum_candidates_not_processed = [
                    cid for cid in context.candidate_ids if cid not in sim_cids
                ]
            except Exception:
                pass
            return True

        from quantum.evaluate import QuantumPipeline
        qm_pipeline = QuantumPipeline(test_fixture_mode=context.synthetic_data_present)
        
        # Determine candidate(s) to simulate
        if config.quantum_policy.quantum_mode == "representative":
            target_var = qm_pipeline.select_demo_variant(config.chemistry_parquet)
            logger.info(f"Quantum representative mode: simulating {target_var}...")
            qm_pipeline.run(
                chem_results_path=config.chemistry_parquet,
                variant_id=target_var,
                enable_noise=config.quantum_policy.enable_noise,
            )
            context.quantum_candidates_processed = [target_var]
            context.quantum_candidates_not_processed = [
                cid for cid in context.candidate_ids if cid != target_var
            ]
        else:
            # All candidates mode
            processed = []
            for cid in context.candidate_ids:
                qm_pipeline.run(
                    chem_results_path=config.chemistry_parquet,
                    variant_id=cid,
                    enable_noise=config.quantum_policy.enable_noise,
                )
                processed.append(cid)
            context.quantum_candidates_processed = processed
            context.quantum_candidates_not_processed = []

        if not qm_path.exists():
            context.record_stage_failure(self.name, 0.0, f"Expected output {qm_path} was not created.")
            return False

        context.output_artifacts["quantum_parquet"] = str(qm_path)
        context.output_artifacts["quantum_manifest_json"] = str(manifest_path)
        context.quantum_backend_type = "SIMULATOR"
        context.integral_backend = "CLASSICAL_FALLBACK"
        return True


class FusionStage(PipelineStage):
    """Stage 7: Performs multimodal evidence fusion, deterministic ranking, and explanation generation."""

    def __init__(self):
        super().__init__(name="fusion", optional=False)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        from fusion.config import FusionConfig
        from fusion.evaluate import run_fusion_pipeline

        fusion_cfg = FusionConfig(
            protein_ai_path=config.protein_ai_parquet,
            uncertainty_path=config.uncertainty_parquet,
            acquisition_path=config.acquisition_parquet,
            chemistry_path=config.chemistry_parquet,
            quantum_path=config.quantum_parquet,
            output_results_parquet=config.fusion_results_parquet,
            output_evidence_matrix_parquet=config.evidence_matrix_parquet,
            output_manifest_json=config.fusion_manifest_json,
            output_explanations_json=config.candidate_explanations_json,
        )

        ranked_candidates, _ = run_fusion_pipeline(config=fusion_cfg, verbose=False)

        if not config.fusion_results_parquet.exists():
            context.record_stage_failure(self.name, 0.0, f"Expected output {config.fusion_results_parquet} missing.")
            return False

        context.output_artifacts["fusion_results_parquet"] = str(config.fusion_results_parquet)
        context.output_artifacts["evidence_matrix_parquet"] = str(config.evidence_matrix_parquet)
        context.output_artifacts["fusion_manifest_json"] = str(config.fusion_manifest_json)
        context.output_artifacts["candidate_explanations_json"] = str(config.candidate_explanations_json)

        # Record final top candidates into context
        context.final_ranking = [
            {
                "rank": c.rank,
                "candidate_id": c.candidate_id,
                "fusion_score": round(c.fusion_score, 4),
                "decision_status": c.decision_status,
                "confidence_label": c.confidence_label,
                "evidence_coverage": f"{c.available_evidence_count}/6",
                "vqe_casci_error": round(c.vqe_casci_error, 6) if c.vqe_casci_error is not None else None,
            }
            for c in ranked_candidates
        ]
        return True
