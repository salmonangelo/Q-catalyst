"""Machine-readable pipeline manifest generator for Phase 7 execution auditability."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pipeline.config import PipelineConfig
from pipeline.context import PipelineContext


class PipelineManifestBuilder:
    """Builds and serializes comprehensive pipeline execution manifests."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

    def build_manifest(self, context: PipelineContext) -> Dict[str, Any]:
        """Constructs the manifest dictionary."""
        return {
            "run_id": context.run_id,
            "timestamp": context.start_time,
            "completion_time": context.end_time,
            "total_duration_seconds": context.total_duration_seconds,
            "pipeline_version": self.config.version,
            "random_seed": context.random_seed,
            "config_hash": context.config_hash,
            "candidates": {
                "count": context.candidate_count,
                "selection_policy": context.candidate_selection_policy,
                "ids": context.candidate_ids,
            },
            "stages": {
                "status": context.stage_status,
                "durations_seconds": context.stage_durations,
                "start_times": context.stage_start_times,
                "end_times": context.stage_end_times,
                "messages": context.stage_messages,
            },
            "artifacts": {
                "inputs": context.input_artifacts,
                "outputs": context.output_artifacts,
            },
            "provenance_and_backends": {
                "data_source": context.data_source,
                "data_quality_flag": context.data_quality_flag,
                "synthetic_data_present": context.synthetic_data_present,
                "quantum_backend_type": context.quantum_backend_type,
                "integral_backend": context.integral_backend,
                "quantum_candidates_processed": context.quantum_candidates_processed,
                "quantum_candidates_not_processed": context.quantum_candidates_not_processed,
            },
            "scientific_claims_policy": {
                "experimental_validation": False,
                "quantum_advantage": False,
                "hardware_execution": False,
                "biological_activity_proven": False,
                "guardrail_statements": [
                    "This pipeline executes computational triage prioritization, NOT experimental proof of enzyme kinetics.",
                    "Quantum simulations run on classical simulator without claiming quantum hardware advantage.",
                    "No biological conversion rates or benchmark performance numbers have been fabricated.",
                ],
            },
            "warnings": context.warnings,
            "errors": context.errors,
            "final_triage_top": context.final_ranking[:10],
        }

    def save(self, context: PipelineContext, output_path: Optional[Path] = None) -> Path:
        """Saves the pipeline manifest JSON to disk."""
        dest = output_path or (context.run_dir / "manifest.json")
        dest.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = self.build_manifest(context)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        return dest
