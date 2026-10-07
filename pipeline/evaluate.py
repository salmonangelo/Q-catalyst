"""CLI and entry point for Phase 7 End-to-End Pipeline Evaluation."""

import argparse
from pathlib import Path
import sys
from typing import Optional
import yaml

from pipeline.config import PipelineConfig, QuantumPolicyConfig
from pipeline.context import PipelineContext
from pipeline.runner import PipelineRunner


def load_pipeline_config(config_path: Path = Path("configs/config.yaml")) -> PipelineConfig:
    """Loads pipeline configuration from project config.yaml if available."""
    if not config_path.exists():
        return PipelineConfig()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        p_dict = raw.get("pipeline", {})
        if not p_dict:
            return PipelineConfig()

        qp_dict = p_dict.get("quantum_policy", {})
        q_policy = QuantumPolicyConfig(**qp_dict) if qp_dict else QuantumPolicyConfig()

        return PipelineConfig(
            pipeline_name=p_dict.get("pipeline_name", "qcatalyst_end_to_end"),
            version=p_dict.get("version", "0.1.0"),
            random_seed=p_dict.get("random_seed", 42),
            output_root=Path(p_dict.get("output_root", "runs")),
            enabled_stages=p_dict.get("enabled_stages", [
                "data", "protein_ai", "uncertainty", "acquisition", "chemistry", "quantum", "fusion"
            ]),
            fail_fast=p_dict.get("fail_fast", True),
            optional_stages=p_dict.get("optional_stages", ["quantum"]),
            reuse_cached_outputs=p_dict.get("reuse_cached_outputs", True),
            candidate_limit=p_dict.get("candidate_limit", None),
            candidate_selection_policy=p_dict.get("candidate_selection_policy", "deterministic_top"),
            quantum_policy=q_policy,
            synthetic_data_policy=p_dict.get("synthetic_data_policy", "preserve_provenance"),
            split_strategy=p_dict.get("split_strategy", "mutation_complexity"),
        )
    except Exception as e:
        print(f"Warning: Failed to parse pipeline config ({e}). Using defaults.")
        return PipelineConfig()


def print_demo_summary(context: PipelineContext, config: PipelineConfig) -> None:
    """Prints a polished, demo-friendly terminal summary of the pipeline execution."""
    print("\n" + "=" * 60)
    print("Q-CATALYST")
    print("Mechanism-Aware Quantum–AI PETase Triage Pipeline")
    print("=" * 60)
    print(f"Pipeline run:  {context.run_id}")
    print(f"Candidates:    {context.candidate_count}")
    print(f"Duration:      {context.total_duration_seconds:.2f}s")
    print(f"Data Source:   {context.data_source} ({context.data_quality_flag})")
    print("-" * 60)

    # Stages status list
    for idx, stage in enumerate(config.enabled_stages, start=1):
        status = context.stage_status.get(stage, "NOT_RUN")
        dur = context.stage_durations.get(stage, 0.0)
        dots = "." * (25 - len(stage))
        print(f"[{idx}/{len(config.enabled_stages)}] {stage.capitalize():<14} {dots} {status:<14} ({dur:.2f}s)")

    print("-" * 60)
    print("FINAL TRIAGE RECOMMENDATIONS")
    print("-" * 60)

    if context.final_ranking:
        for c in context.final_ranking[:5]:
            err_info = f"VQE err={c['vqe_casci_error']:.4f} Ha" if c.get("vqe_casci_error") is not None else "QM=N/A"
            print(f"  #{c['rank']:2d}  {c['candidate_id']:<14} Score: {c['fusion_score']:.4f}  "
                  f"Status: {c['decision_status']:<22} Coverage: {c['evidence_coverage']}  "
                  f"Conf: {c['confidence_label']:<18} [{err_info}]")
    else:
        print("  *No candidates were prioritized.*")

    print("-" * 60)
    print("QUANTUM PROVENANCE")
    print("-" * 60)
    print(f"Backend:           {context.quantum_backend_type} (Qiskit Statevector / Aer)")
    print(f"Integral Backend:  {context.integral_backend}")
    print(f"Simulated Active:  (4e, 4o) -> 8 Qubits (Jordan-Wigner)")
    print(f"Simulated Variants: {len(context.quantum_candidates_processed)} ({', '.join(context.quantum_candidates_processed) if context.quantum_candidates_processed else 'None'})")
    print("-" * 60)
    print("SCIENTIFIC STATUS")
    print("-" * 60)
    print(f"Experimental Validation: NOT AVAILABLE (Computational triage only)")
    print(f"Physical Quantum Hardware: NO (Classical simulator)")
    print(f"Quantum Advantage Claim:   NOT CLAIMED")
    print("-" * 60)
    print(f"Run complete. Artifacts saved to: {context.run_dir}")
    print("=" * 60 + "\n")


def run_pipeline_cli(config: Optional[PipelineConfig] = None) -> PipelineContext:
    """Entry point for programmatic or CLI execution."""
    cfg = config or load_pipeline_config()
    runner = PipelineRunner(cfg)
    context = runner.run()
    print_demo_summary(context, cfg)
    return context


def main():
    """CLI argument parser."""
    parser = argparse.ArgumentParser(description="Q-Catalyst End-to-End Pipeline Orchestrator")
    parser.add_argument("--config", type=str, default="configs/config.yaml", help="Path to config.yaml")
    parser.add_argument("--candidate-limit", type=int, default=None, help="Limit number of candidates")
    parser.add_argument("--quantum-mode", type=str, choices=["representative", "all"], default=None, help="Quantum mode")
    parser.add_argument("--no-cache", action="store_true", help="Disable output caching")
    args = parser.parse_args()

    cfg = load_pipeline_config(Path(args.config))
    if args.candidate_limit is not None:
        cfg.candidate_limit = args.candidate_limit
    if args.quantum_mode is not None:
        cfg.quantum_policy.quantum_mode = args.quantum_mode
    if args.no_cache:
        cfg.reuse_cached_outputs = False

    run_pipeline_cli(cfg)


if __name__ == "__main__":
    main()
