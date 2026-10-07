"""Unit tests for Phase 7 Pipeline Orchestration components."""

from pathlib import Path
import pytest
import pandas as pd

from pipeline.config import PipelineConfig, QuantumPolicyConfig
from pipeline.context import PipelineContext, StageStatus, create_pipeline_context
from pipeline.manifest import PipelineManifestBuilder
from pipeline.report import PipelineReportGenerator
from pipeline.runner import PipelineRunner
from pipeline.stages import PipelineStage


class MockSuccessStage(PipelineStage):
    def __init__(self, name: str = "mock_stage"):
        super().__init__(name=name, optional=False)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        context.output_artifacts["mock_out"] = "mock_path.parquet"
        return True


class MockFailureStage(PipelineStage):
    def __init__(self, name: str = "failing_stage", optional: bool = False):
        super().__init__(name=name, optional=optional)

    def run(self, context: PipelineContext, config: PipelineConfig) -> bool:
        context.record_stage_failure(self.name, 0.01, "Simulated stage error.")
        return False


def test_pipeline_config_defaults():
    """Verify PipelineConfig defaults and structure."""
    cfg = PipelineConfig()
    assert "data" in cfg.enabled_stages
    assert "fusion" in cfg.enabled_stages
    assert cfg.fail_fast is True
    assert cfg.quantum_policy.quantum_mode == "representative"
    assert cfg.random_seed == 42


def test_pipeline_context_tracking(tmp_path: Path):
    """Verify context lifecycle transitions and duration tracking."""
    ctx = create_pipeline_context(output_root=tmp_path, random_seed=42)
    assert ctx.run_dir.exists()
    assert (ctx.run_dir / "logs").exists()
    assert (ctx.run_dir / "outputs").exists()

    ctx.record_stage_start("data")
    assert ctx.stage_status["data"] == StageStatus.RUNNING.value

    ctx.record_stage_success("data", duration_sec=1.23, cached=False)
    assert ctx.stage_status["data"] == StageStatus.SUCCESS.value
    assert ctx.stage_durations["data"] == 1.23

    ctx.record_stage_skipped("quantum", reason="Optional stage disabled")
    assert ctx.stage_status["quantum"] == StageStatus.SKIPPED.value

    ctx.finalize()
    assert ctx.end_time is not None
    assert ctx.total_duration_seconds >= 0.0


def test_pipeline_runner_fail_fast_policy(tmp_path: Path):
    """Verify that mandatory stage failures abort subsequent stages when fail_fast=True."""
    cfg = PipelineConfig(
        output_root=tmp_path,
        enabled_stages=["stage_1", "stage_2", "stage_3"],
        optional_stages=[],
        fail_fast=True,
    )
    runner = PipelineRunner(cfg)
    runner.stage_registry = {
        "stage_1": MockSuccessStage("stage_1"),
        "stage_2": MockFailureStage("stage_2", optional=False),
        "stage_3": MockSuccessStage("stage_3"),
    }

    ctx = runner.run(cfg)
    assert ctx.stage_status["stage_1"] == StageStatus.SUCCESS.value
    assert ctx.stage_status["stage_2"] == StageStatus.FAILED.value
    assert ctx.stage_status["stage_3"] == StageStatus.SKIPPED.value


def test_pipeline_runner_optional_stage_continuation(tmp_path: Path):
    """Verify that optional stage failures do not abort subsequent stages."""
    cfg = PipelineConfig(
        output_root=tmp_path,
        enabled_stages=["stage_1", "stage_2", "stage_3"],
        optional_stages=["stage_2"],
        fail_fast=True,
    )
    runner = PipelineRunner(cfg)
    runner.stage_registry = {
        "stage_1": MockSuccessStage("stage_1"),
        "stage_2": MockFailureStage("stage_2", optional=True),
        "stage_3": MockSuccessStage("stage_3"),
    }

    ctx = runner.run(cfg)
    assert ctx.stage_status["stage_1"] == StageStatus.SUCCESS.value
    assert ctx.stage_status["stage_2"] == StageStatus.FAILED.value
    assert ctx.stage_status["stage_3"] == StageStatus.SUCCESS.value


def test_pipeline_manifest_and_report_generation(tmp_path: Path):
    """Verify manifest JSON and Markdown report formatting."""
    cfg = PipelineConfig(output_root=tmp_path)
    ctx = create_pipeline_context(output_root=tmp_path)
    ctx.candidate_count = 5
    ctx.candidate_ids = ["VAR_1", "VAR_2", "VAR_3", "VAR_4", "VAR_5"]
    ctx.stage_status = {"data": "SUCCESS", "quantum": "SUCCESS"}
    ctx.stage_durations = {"data": 0.5, "quantum": 1.5}
    ctx.quantum_backend_type = "SIMULATOR"
    ctx.integral_backend = "CLASSICAL_FALLBACK"
    ctx.final_ranking = [
        {
            "rank": 1,
            "candidate_id": "VAR_1",
            "fusion_score": 0.85,
            "decision_status": "PRIORITIZE",
            "confidence_label": "HIGH_CONFIDENCE",
            "evidence_coverage": "6/6",
            "vqe_casci_error": 0.0092,
        }
    ]
    ctx.finalize()

    manifest_builder = PipelineManifestBuilder(cfg)
    manifest_path = manifest_builder.save(ctx)
    assert manifest_path.exists()

    report_gen = PipelineReportGenerator(cfg)
    report_paths = report_gen.save_reports(ctx)
    assert report_paths["markdown_report"].exists()
    assert report_paths["json_report"].exists()

    with open(report_paths["markdown_report"], "r", encoding="utf-8") as f:
        md_content = f.read()

    assert "# Q-CATALYST Pipeline Execution Report" in md_content
    assert "SIMULATOR" in md_content
    assert "VAR_1" in md_content
    assert "PRIORITIZE" in md_content
