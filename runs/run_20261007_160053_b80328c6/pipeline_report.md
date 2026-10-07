# Q-CATALYST Pipeline Execution Report

**Run ID**: `run_20261007_160053_b80328c6`  
**Timestamp**: 2026-10-07T16:00:53.834138+00:00  
**Total Runtime**: 8.96 seconds  
**Configuration Hash**: `b80328c6`  
**Random Seed**: `42`  

## 1. Run Summary

- **Candidates Evaluated**: 1
- **Stages Configured**: 7
- **Data Source**: `discovered_downstream_artifacts` (INFERRED_CANDIDATES)
- **Synthetic Test Fixtures Present**: NO
- **Quantum Simulation Backend**: `SIMULATOR`
- **Integral Backend**: `CLASSICAL_FALLBACK`

## 2. Stage Execution Status

| Stage Name | Status | Duration (s) | Message / Notes |
| :--- | :--- | :--- | :--- |
| `data` | **SUCCESS** | 0.06s | - |
| `protein_ai` | **FAILED** | 8.90s | Unhandled exception in stage 'protein_ai': Curated variants dataset not found at 'data\curated\variants.parquet'.
Please run 'python data/build_dataset.py' with raw benchmark data first. |
| `uncertainty` | **SKIPPED** | 0.00s | Previous mandatory stage failed. |
| `acquisition` | **SKIPPED** | 0.00s | Previous mandatory stage failed. |
| `chemistry` | **SKIPPED** | 0.00s | Previous mandatory stage failed. |
| `quantum` | **SKIPPED** | 0.00s | Previous mandatory stage failed. |
| `fusion` | **SKIPPED** | 0.00s | Previous mandatory stage failed. |

## 3. Protein AI & Uncertainty Estimation

- **Model Representation**: ESM Embeddings + Mutation Masked Log-Likelihood Ratio Scoring.
- **Uncertainty Triad**: 10-member Ensemble Disagreement, Embedding-space OOD distance, Split Conformal Calibration.
- **Predictions Artifact**: `N/A`
- **Uncertainty Artifact**: `N/A`

## 4. Mechanism-Aware Acquisition

- **Catalytic Reference**: *Is*PETase PDB `5XJH` (Ser160, Asp206, His237 triad).
- **Acquisition Criteria**: Multi-objective balance of sequence fitness, uncertainty, active-site proximity, and sequence diversity.
- **Selected Candidates Artifact**: `N/A`

## 5. Classical Chemistry Modeling

- **Active-Site Cluster**: Reduced 7-residue catalytic pocket extracted from 5XJH.
- **Electronic Structure**: Hartree-Fock (HF/STO-3G) baseline with SCF convergence verification.
- **Chemistry Results Artifact**: `N/A`

## 6. Quantum Simulation

- **Active Space**: $(4e, 4o)$ active space (8 qubits via Jordan-Wigner transformation).
- **Exact Solver Reference**: CASCI matrix diagonalization in particle-conserving Fock subspace.
- **VQE Algorithm**: Parameterized `TwoLocal` ($R_y + CZ$) ansatz with `COBYLA` optimizer.
- **Execution Backend**: `SIMULATOR` (Classical statevector / Aer simulation).
- **Simulated Candidates**: 0 (None)
- **Quantum Artifact**: `N/A`

## 7. Final Triage Ranking & Evidence Fusion

*No final ranking records generated.*

## 8. Provenance & Scientific Guardrails

> [!IMPORTANT]
> **Computational Triage Guardrail**: This ranking is a computational hypothesis generation tool to prioritize enzyme variants for laboratory synthesis. It is **NOT** experimental proof of biological activity or PET degradation.

- **No Quantum Hardware**: Quantum simulations are executed on classical statevector simulators.
- **No Quantum Advantage Claimed**: The quantum algorithm serves as an active-space electronic structure benchmark.
- **Data Integrity**: No empirical PET-Gym metrics or conversion rates were fabricated.

## 9. Reproducibility Metadata

- **Random Seed**: `42`
- **Configuration Hash**: `b80328c6`
- **Pipeline Version**: `0.1.0`
- **Run Artifacts Root**: `runs\run_20261007_160053_b80328c6`
