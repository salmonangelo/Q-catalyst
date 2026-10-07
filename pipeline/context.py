"""Pipeline Context tracking execution state, artifacts, timestamps, and stage statuses."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class StageStatus(str, Enum):
    """Standard lifecycle states for pipeline stages."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    SUCCESS_CACHED = "SUCCESS_CACHED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass
class PipelineContext:
    """Consolidated state and audit log for a single end-to-end pipeline execution run."""
    run_id: str
    run_dir: Path
    random_seed: int
    config_hash: str
    
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    total_duration_seconds: float = 0.0
    
    # Candidate metadata
    candidate_count: int = 0
    candidate_ids: List[str] = field(default_factory=list)
    candidate_selection_policy: str = "deterministic_top"
    
    # Stage execution tracking
    stage_status: Dict[str, str] = field(default_factory=dict)
    stage_start_times: Dict[str, str] = field(default_factory=dict)
    stage_end_times: Dict[str, str] = field(default_factory=dict)
    stage_durations: Dict[str, float] = field(default_factory=dict)
    stage_messages: Dict[str, str] = field(default_factory=dict)
    
    # Artifact registries
    input_artifacts: Dict[str, str] = field(default_factory=dict)
    output_artifacts: Dict[str, str] = field(default_factory=dict)
    
    # Logging & error tracking
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Scientific provenance
    data_source: str = "curated_variants"
    data_quality_flag: str = "VERIFIED_DATA"
    synthetic_data_present: bool = False
    quantum_backend_type: str = "SIMULATOR"
    integral_backend: str = "CLASSICAL_FALLBACK"
    quantum_candidates_processed: List[str] = field(default_factory=list)
    quantum_candidates_not_processed: List[str] = field(default_factory=list)
    
    # Final triage results summary
    final_ranking: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def logs_dir(self) -> Path:
        return self.run_dir / "logs"

    @property
    def outputs_dir(self) -> Path:
        return self.run_dir / "outputs"

    def record_stage_start(self, stage_name: str) -> None:
        """Mark stage as running and record start timestamp."""
        self.stage_status[stage_name] = StageStatus.RUNNING.value
        self.stage_start_times[stage_name] = datetime.now(timezone.utc).isoformat()

    def record_stage_success(self, stage_name: str, duration_sec: float, cached: bool = False, msg: str = "") -> None:
        """Record successful stage execution."""
        status = StageStatus.SUCCESS_CACHED if cached else StageStatus.SUCCESS
        self.stage_status[stage_name] = status.value
        self.stage_end_times[stage_name] = datetime.now(timezone.utc).isoformat()
        self.stage_durations[stage_name] = round(duration_sec, 4)
        if msg:
            self.stage_messages[stage_name] = msg

    def record_stage_failure(self, stage_name: str, duration_sec: float, error_msg: str) -> None:
        """Record stage execution failure."""
        self.stage_status[stage_name] = StageStatus.FAILED.value
        self.stage_end_times[stage_name] = datetime.now(timezone.utc).isoformat()
        self.stage_durations[stage_name] = round(duration_sec, 4)
        self.stage_messages[stage_name] = error_msg
        self.errors.append(f"Stage '{stage_name}' failed: {error_msg}")

    def record_stage_skipped(self, stage_name: str, reason: str) -> None:
        """Record skipped stage."""
        self.stage_status[stage_name] = StageStatus.SKIPPED.value
        self.stage_durations[stage_name] = 0.0
        self.stage_messages[stage_name] = reason

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def finalize(self) -> None:
        """Computes total pipeline runtime and marks completion."""
        self.end_time = datetime.now(timezone.utc).isoformat()
        try:
            t_start = datetime.fromisoformat(self.start_time)
            t_end = datetime.fromisoformat(self.end_time)
            self.total_duration_seconds = round((t_end - t_start).total_seconds(), 4)
        except Exception:
            self.total_duration_seconds = sum(self.stage_durations.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to serializable dictionary."""
        d = asdict(self)
        d["run_dir"] = str(self.run_dir)
        return d


def create_pipeline_context(
    output_root: Path = Path("runs"),
    random_seed: int = 42,
    config_dict: Optional[Dict[str, Any]] = None,
) -> PipelineContext:
    """Instantiates a new PipelineContext with deterministic ID and created directories."""
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_cfg = json.dumps(config_dict or {}, sort_keys=True)
    cfg_hash = hashlib.sha256(raw_cfg.encode("utf-8")).hexdigest()[:8]
    
    run_id = f"run_{timestamp_str}_{cfg_hash}"
    run_dir = Path(output_root) / run_id
    
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)
    
    return PipelineContext(
        run_id=run_id,
        run_dir=run_dir,
        random_seed=random_seed,
        config_hash=cfg_hash,
    )
