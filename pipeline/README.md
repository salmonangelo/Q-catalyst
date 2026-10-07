# Phase 7: End-to-End Pipeline Orchestration

## 1. Overview & Architecture

The **Q-Catalyst Pipeline Orchestrator** automates the multi-stage hybrid quantum-classical triage workflow from candidate input to final evidence-fused prioritization:

$$\text{Data} \longrightarrow \text{Protein-AI} \longrightarrow \text{Uncertainty} \longrightarrow \text{Acquisition} \longrightarrow \text{Chemistry} \longrightarrow \text{Quantum} \longrightarrow \text{Fusion} \longrightarrow \text{Report}$$

```
                ┌──────────────────────────────┐
                │     1. Data Foundation       │
                │  (Variants, Mutations, PDB)  │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │      2. Protein AI           │
                │    (ESM2-8M Fitness Pred)    │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │       3. Uncertainty         │
                │ (Ensemble + OOD + Conformal) │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │   4. Smart Acquisition Gate  │
                │ (Mechanism Proximity + Div)  │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │   5. Classical Chemistry     │
                │(5XJH Active Site HF Cluster) │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │   6. Quantum Simulation      │
                │  (4e, 4o / 8-Qubit VQE/CASCI)│
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │     7. Evidence Fusion       │
                │ (Multimodal Decision Engine) │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │   FINAL AUDITABLE REPORT     │
                │    (runs/<run_id>/report)    │
                └──────────────────────────────┘
```

---

## 2. Stage Execution Order

1. **`data`**: Validates curated variants (`data/curated/variants.parquet`), checks data quality flags, and extracts candidate batches.
2. **`protein_ai`**: Computes zero-shot ESM sequence fitness and supervised regression predictions (`protein_ai/predictions.parquet`).
3. **`uncertainty`**: Calculates 10-member ensemble disagreement, OOD manifold distance, conformal intervals, and Gate 0 verification (`uncertainty/uncertainty.parquet`).
4. **`acquisition`**: Performs multi-objective optimization balancing fitness, uncertainty, active-site structural proximity (to Ser160, Asp206, His237), and sequence diversity (`acquisition/selected_candidates.parquet`).
5. **`chemistry`**: Extracts the 7-residue catalytic cluster from PDB `5XJH`, validates geometry without steric clashes, and calculates HF/STO-3G classical electronic structure (`chemistry/chem_results.parquet`).
6. **`quantum`**: Constructs $(4e, 4o)$ active space, Jordan-Wigner 8-qubit Hamiltonian, exact classical CASCI reference, and VQE energy convergence (`quantum/quantum_results.parquet`).
7. **`fusion`**: Multi-channel weighted linear combination, evidence coverage evaluation, confidence labeling, deterministic tie-breaking, and rule-based explainability (`fusion/fusion_results.parquet`).

---

## 3. Configuration & Policies

Master pipeline settings are configured in `configs/config.yaml`:

```yaml
pipeline:
  enabled_stages:
    - data
    - protein_ai
    - uncertainty
    - acquisition
    - chemistry
    - quantum
    - fusion
  fail_fast: true
  optional_stages:
    - quantum
  reuse_cached_outputs: true
  candidate_limit: 10
  quantum_policy:
    quantum_mode: "representative"  # 'representative' or 'all'
    representative_selection: "top_ranked"
    enable_noise: false
```

### Caching Behavior (`reuse_cached_outputs: true`)
Stages check for valid upstream Parquet contracts and manifests. Valid cached outputs are reused without redundant compute, marking stage status as `SUCCESS_CACHED`.

### Failure Handling
- **Mandatory Stages**: If data, AI, uncertainty, acquisition, chemistry, or fusion fail, the pipeline halts immediately (when `fail_fast = true`).
- **Optional Stages**: The `quantum` simulation stage is marked optional by default; if quantum simulation is unavailable or fails, the pipeline logs a non-fatal warning and executes classical-only evidence fusion.

---

## 4. Quantum Simulation Provenance

- **Backend**: Classical simulation using Qiskit Statevector / Aer (`quantum_backend_type = "SIMULATOR"`).
- **Integrals**: Model-derived active space integrals (`integral_backend = "CLASSICAL_FALLBACK"`).
- **Physical Hardware**: No quantum hardware execution or quantum advantage is claimed.

---

## 5. Execution

To execute the entire end-to-end pipeline:

```bash
python -m pipeline.evaluate
```

Outputs are structured inside `runs/<run_id>/`:
- `manifest.json`: Full machine-readable audit trail and provenance.
- `pipeline_report.json`: Execution metrics, stage durations, and final candidate scores.
- `pipeline_report.md`: Human-readable summary report.
- `logs/pipeline.log`: Execution log stream.
