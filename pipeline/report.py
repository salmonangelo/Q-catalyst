"""Human-readable and structured report generation for pipeline execution runs."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pipeline.config import PipelineConfig
from pipeline.context import PipelineContext


class PipelineReportGenerator:
    """Generates structured JSON and human-readable Markdown pipeline execution reports."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

    def generate_markdown_report(self, context: PipelineContext) -> str:
        """Constructs human-readable Markdown summary of the entire end-to-end run."""
        lines = []
        lines.append("# Q-CATALYST Pipeline Execution Report")
        lines.append("")
        lines.append(f"**Run ID**: `{context.run_id}`  ")
        lines.append(f"**Timestamp**: {context.start_time}  ")
        lines.append(f"**Total Runtime**: {context.total_duration_seconds:.2f} seconds  ")
        lines.append(f"**Configuration Hash**: `{context.config_hash}`  ")
        lines.append(f"**Random Seed**: `{context.random_seed}`  ")
        lines.append("")

        # 1. Run Summary
        lines.append("## 1. Run Summary")
        lines.append("")
        lines.append(f"- **Candidates Evaluated**: {context.candidate_count}")
        lines.append(f"- **Stages Configured**: {len(self.config.enabled_stages)}")
        lines.append(f"- **Data Source**: `{context.data_source}` ({context.data_quality_flag})")
        lines.append(f"- **Synthetic Test Fixtures Present**: {'YES' if context.synthetic_data_present else 'NO'}")
        lines.append(f"- **Quantum Simulation Backend**: `{context.quantum_backend_type}`")
        lines.append(f"- **Integral Backend**: `{context.integral_backend}`")
        lines.append("")

        # 2. Stage Execution Status
        lines.append("## 2. Stage Execution Status")
        lines.append("")
        lines.append("| Stage Name | Status | Duration (s) | Message / Notes |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for stage in self.config.enabled_stages:
            status = context.stage_status.get(stage, "NOT_RUN")
            dur = context.stage_durations.get(stage, 0.0)
            msg = context.stage_messages.get(stage, "-")
            lines.append(f"| `{stage}` | **{status}** | {dur:.2f}s | {msg} |")
        lines.append("")

        # 3. Protein AI & Uncertainty
        lines.append("## 3. Protein AI & Uncertainty Estimation")
        lines.append("")
        lines.append("- **Model Representation**: ESM Embeddings + Mutation Masked Log-Likelihood Ratio Scoring.")
        lines.append("- **Uncertainty Triad**: 10-member Ensemble Disagreement, Embedding-space OOD distance, Split Conformal Calibration.")
        lines.append(f"- **Predictions Artifact**: `{context.output_artifacts.get('protein_ai_parquet', 'N/A')}`")
        lines.append(f"- **Uncertainty Artifact**: `{context.output_artifacts.get('uncertainty_parquet', 'N/A')}`")
        lines.append("")

        # 4. Mechanism-Aware Acquisition
        lines.append("## 4. Mechanism-Aware Acquisition")
        lines.append("")
        lines.append("- **Catalytic Reference**: *Is*PETase PDB `5XJH` (Ser160, Asp206, His237 triad).")
        lines.append("- **Acquisition Criteria**: Multi-objective balance of sequence fitness, uncertainty, active-site proximity, and sequence diversity.")
        lines.append(f"- **Selected Candidates Artifact**: `{context.output_artifacts.get('acquisition_parquet', 'N/A')}`")
        lines.append("")

        # 5. Classical Chemistry
        lines.append("## 5. Classical Chemistry Modeling")
        lines.append("")
        lines.append("- **Active-Site Cluster**: Reduced 7-residue catalytic pocket extracted from 5XJH.")
        lines.append("- **Electronic Structure**: Hartree-Fock (HF/STO-3G) baseline with SCF convergence verification.")
        lines.append(f"- **Chemistry Results Artifact**: `{context.output_artifacts.get('chemistry_parquet', 'N/A')}`")
        lines.append("")

        # 6. Quantum Simulation
        lines.append("## 6. Quantum Simulation")
        lines.append("")
        lines.append("- **Active Space**: $(4e, 4o)$ active space (8 qubits via Jordan-Wigner transformation).")
        lines.append("- **Exact Solver Reference**: CASCI matrix diagonalization in particle-conserving Fock subspace.")
        lines.append("- **VQE Algorithm**: Parameterized `TwoLocal` ($R_y + CZ$) ansatz with `COBYLA` optimizer.")
        lines.append(f"- **Execution Backend**: `{context.quantum_backend_type}` (Classical statevector / Aer simulation).")
        lines.append(f"- **Simulated Candidates**: {len(context.quantum_candidates_processed)} ({', '.join(context.quantum_candidates_processed) if context.quantum_candidates_processed else 'None'})")
        lines.append(f"- **Quantum Artifact**: `{context.output_artifacts.get('quantum_parquet', 'N/A')}`")
        lines.append("")

        # 7. Final Ranked Candidates
        lines.append("## 7. Final Triage Ranking & Evidence Fusion")
        lines.append("")
        if context.final_ranking:
            lines.append("| Rank | Candidate ID | Fusion Score | Decision Status | Confidence | Coverage | VQE Error (Ha) |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for c in context.final_ranking[:10]:
                err_str = f"{c['vqe_casci_error']:.4f}" if c.get("vqe_casci_error") is not None else "N/A"
                lines.append(
                    f"| #{c['rank']} | **{c['candidate_id']}** | {c['fusion_score']:.4f} | "
                    f"`{c['decision_status']}` | `{c['confidence_label']}` | {c['evidence_coverage']} | {err_str} |"
                )
        else:
            lines.append("*No final ranking records generated.*")
        lines.append("")

        # 8. Provenance & Limitations
        lines.append("## 8. Provenance & Scientific Guardrails")
        lines.append("")
        lines.append("> [!IMPORTANT]")
        lines.append("> **Computational Triage Guardrail**: This ranking is a computational hypothesis generation tool to prioritize enzyme variants for laboratory synthesis. It is **NOT** experimental proof of biological activity or PET degradation.")
        lines.append("")
        lines.append("- **No Quantum Hardware**: Quantum simulations are executed on classical statevector simulators.")
        lines.append("- **No Quantum Advantage Claimed**: The quantum algorithm serves as an active-space electronic structure benchmark.")
        lines.append("- **Data Integrity**: No empirical PET-Gym metrics or conversion rates were fabricated.")
        lines.append("")

        # 9. Reproducibility
        lines.append("## 9. Reproducibility Metadata")
        lines.append("")
        lines.append(f"- **Random Seed**: `{context.random_seed}`")
        lines.append(f"- **Configuration Hash**: `{context.config_hash}`")
        lines.append(f"- **Pipeline Version**: `{self.config.version}`")
        lines.append(f"- **Run Artifacts Root**: `{context.run_dir}`")
        lines.append("")

        return "\n".join(lines)

    def save_reports(self, context: PipelineContext) -> Dict[str, Path]:
        """Writes both markdown and JSON reports into the run directory."""
        md_text = self.generate_markdown_report(context)
        md_path = context.run_dir / "pipeline_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        json_data = {
            "run_id": context.run_id,
            "timestamp": context.start_time,
            "completion_time": context.end_time,
            "total_duration_seconds": context.total_duration_seconds,
            "candidates_count": context.candidate_count,
            "stage_status": context.stage_status,
            "stage_durations": context.stage_durations,
            "quantum_backend": context.quantum_backend_type,
            "integral_backend": context.integral_backend,
            "final_ranking": context.final_ranking,
            "warnings": context.warnings,
            "errors": context.errors,
        }
        json_path = context.run_dir / "pipeline_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        return {"markdown_report": md_path, "json_report": json_path}
