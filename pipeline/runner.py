"""End-to-end PipelineRunner orchestrator for Q-Catalyst."""

import logging
from pathlib import Path
import random
import time
from typing import Dict, List, Optional
import numpy as np

from pipeline.config import PipelineConfig
from pipeline.context import PipelineContext, StageStatus, create_pipeline_context
from pipeline.manifest import PipelineManifestBuilder
from pipeline.report import PipelineReportGenerator
from pipeline.stages import (
    AcquisitionStage,
    ChemistryStage,
    DataStage,
    FusionStage,
    PipelineStage,
    ProteinAIStage,
    QuantumStage,
    UncertaintyStage,
)


def setup_pipeline_logger(log_file: Path) -> logging.Logger:
    """Configures dedicated file and console logging for a pipeline execution run."""
    logger = logging.getLogger("QCatalyst-PipelineRunner")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return logger


class PipelineRunner:
    """Orchestrates end-to-end multi-stage pipeline execution with error handling and auditing."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.stage_registry: Dict[str, PipelineStage] = {
            "data": DataStage(),
            "protein_ai": ProteinAIStage(),
            "uncertainty": UncertaintyStage(),
            "acquisition": AcquisitionStage(),
            "chemistry": ChemistryStage(),
            "quantum": QuantumStage(),
            "fusion": FusionStage(),
        }
        self.manifest_builder = PipelineManifestBuilder(self.config)
        self.report_generator = PipelineReportGenerator(self.config)

    def _set_deterministic_seed(self, seed: int) -> None:
        """Sets random seeds across Python and NumPy for reproducible execution."""
        random.seed(seed)
        np.random.seed(seed)

    def run(self, config: Optional[PipelineConfig] = None) -> PipelineContext:
        """Executes the full pipeline workflow across all configured stages."""
        cfg = config or self.config
        self._set_deterministic_seed(cfg.random_seed)

        # 1. Create Run Context
        context = create_pipeline_context(
            output_root=cfg.output_root,
            random_seed=cfg.random_seed,
            config_dict=cfg.model_dump(mode="json"),
        )

        log_file = context.logs_dir / "pipeline.log"
        logger = setup_pipeline_logger(log_file)
        logger.info(f"Starting Q-Catalyst Pipeline Run: {context.run_id}")
        logger.info(f"Output directory: {context.run_dir}")
        logger.info(f"Enabled stages: {cfg.enabled_stages}")

        # 2. Iterate through configured stages
        stages_to_run = cfg.enabled_stages
        stage_aborted = False

        for idx, stage_name in enumerate(stages_to_run, start=1):
            if stage_aborted:
                context.record_stage_skipped(stage_name, "Previous mandatory stage failed.")
                continue

            stage = self.stage_registry.get(stage_name)
            if not stage:
                logger.warning(f"Unknown stage '{stage_name}', skipping.")
                context.record_stage_skipped(stage_name, f"Unknown stage '{stage_name}'")
                continue

            logger.info(f"[{idx}/{len(stages_to_run)}] Executing stage: {stage_name.upper()}...")
            context.record_stage_start(stage_name)
            t0 = time.time()

            try:
                success = stage.run(context, cfg)
                duration = time.time() - t0

                if success:
                    context.record_stage_success(stage_name, duration)
                    logger.info(f"Stage '{stage_name}' completed successfully in {duration:.2f}s.")
                else:
                    duration = time.time() - t0
                    error_msg = context.stage_messages.get(stage_name, "Stage execution failed.")
                    logger.error(f"Stage '{stage_name}' failed after {duration:.2f}s: {error_msg}")

                    # Check optional / fail_fast policy
                    if stage_name in cfg.optional_stages:
                        logger.warning(f"Stage '{stage_name}' is optional. Pipeline continuing.")
                    elif cfg.fail_fast:
                        logger.error(f"Mandatory stage '{stage_name}' failed with fail_fast=True. Aborting remaining stages.")
                        stage_aborted = True

            except Exception as e:
                duration = time.time() - t0
                error_msg = f"Unhandled exception in stage '{stage_name}': {e}"
                logger.exception(error_msg)
                context.record_stage_failure(stage_name, duration, error_msg)

                if stage_name in cfg.optional_stages:
                    logger.warning(f"Optional stage '{stage_name}' encountered error. Pipeline continuing.")
                elif cfg.fail_fast:
                    logger.error(f"Mandatory stage '{stage_name}' failed. Aborting.")
                    stage_aborted = True

        # 3. Finalize run context
        context.finalize()
        logger.info(f"Pipeline finished in {context.total_duration_seconds:.2f} seconds.")

        # 4. Save Manifest & Reports
        self.manifest_builder.save(context)
        self.report_generator.save_reports(context)
        logger.info(f"Saved run manifest and execution reports to: {context.run_dir}")

        return context
