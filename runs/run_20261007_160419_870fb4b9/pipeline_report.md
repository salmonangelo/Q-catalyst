# Q-CATALYST Pipeline Execution Report

**Run ID**: `run_20261007_160419_870fb4b9`  
**Timestamp**: 2026-10-07T16:04:19.281773+00:00  
**Total Runtime**: 11.70 seconds  
**Configuration Hash**: `870fb4b9`  
**Random Seed**: `42`  

## 1. Run Summary

- **Candidates Evaluated**: 6
- **Stages Configured**: 7
- **Data Source**: `curated_variants` (VERIFIED_DATA)
- **Synthetic Test Fixtures Present**: NO
- **Quantum Simulation Backend**: `SIMULATOR`
- **Integral Backend**: `CLASSICAL_FALLBACK`

## 2. Stage Execution Status

| Stage Name | Status | Duration (s) | Message / Notes |
| :--- | :--- | :--- | :--- |
| `data` | **SUCCESS** | 0.04s | - |
| `protein_ai` | **SUCCESS** | 8.94s | - |
| `uncertainty` | **SUCCESS** | 1.96s | - |
| `acquisition` | **SUCCESS** | 0.08s | - |
| `chemistry` | **SUCCESS** | 0.10s | - |
| `quantum` | **SUCCESS** | 0.54s | - |
| `fusion` | **SUCCESS** | 0.04s | - |

## 3. Protein AI & Uncertainty Estimation

- **Model Representation**: ESM Embeddings + Mutation Masked Log-Likelihood Ratio Scoring.
- **Uncertainty Triad**: 10-member Ensemble Disagreement, Embedding-space OOD distance, Split Conformal Calibration.
- **Predictions Artifact**: `protein_ai\predictions.parquet`
- **Uncertainty Artifact**: `uncertainty\uncertainty.parquet`

## 4. Mechanism-Aware Acquisition

- **Catalytic Reference**: *Is*PETase PDB `5XJH` (Ser160, Asp206, His237 triad).
- **Acquisition Criteria**: Multi-objective balance of sequence fitness, uncertainty, active-site proximity, and sequence diversity.
- **Selected Candidates Artifact**: `acquisition\selected_candidates.parquet`

## 5. Classical Chemistry Modeling

- **Active-Site Cluster**: Reduced 7-residue catalytic pocket extracted from 5XJH.
- **Electronic Structure**: Hartree-Fock (HF/STO-3G) baseline with SCF convergence verification.
- **Chemistry Results Artifact**: `chemistry\chem_results.parquet`

## 6. Quantum Simulation

- **Active Space**: $(4e, 4o)$ active space (8 qubits via Jordan-Wigner transformation).
- **Exact Solver Reference**: CASCI matrix diagonalization in particle-conserving Fock subspace.
- **VQE Algorithm**: Parameterized `TwoLocal` ($R_y + CZ$) ansatz with `COBYLA` optimizer.
- **Execution Backend**: `SIMULATOR` (Classical statevector / Aer simulation).
- **Simulated Candidates**: 1 (VAR_WT)
- **Quantum Artifact**: `quantum\quantum_results.parquet`

## 7. Final Triage Ranking & Evidence Fusion

| Rank | Candidate ID | Fusion Score | Decision Status | Confidence | Coverage | VQE Error (Ha) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| #1 | **VAR_W132H** | 0.8219 | `PRIORITIZE` | `MODERATE_CONFIDENCE` | 5/6 | N/A |
| #2 | **VAR_WT** | 0.6304 | `PROMISING_BUT_UNCERTAIN` | `MODERATE_CONFIDENCE` | 6/6 | 0.0093 |
| #3 | **VAR_S133G_D179G** | 0.5538 | `PROMISING_BUT_UNCERTAIN` | `LOW_CONFIDENCE` | 5/6 | N/A |
| #4 | **VAR_D179A** | 0.3006 | `INSUFFICIENT_EVIDENCE` | `LOW_CONFIDENCE` | 2/6 | N/A |
| #5 | **VAR_S133A** | 0.2936 | `INSUFFICIENT_EVIDENCE` | `LOW_CONFIDENCE` | 2/6 | N/A |
| #6 | **VAR_H210A** | 0.2749 | `INSUFFICIENT_EVIDENCE` | `LOW_CONFIDENCE` | 2/6 | N/A |

## 8. Provenance & Scientific Guardrails

> [!IMPORTANT]
> **Computational Triage Guardrail**: This ranking is a computational hypothesis generation tool to prioritize enzyme variants for laboratory synthesis. It is **NOT** experimental proof of biological activity or PET degradation.

- **No Quantum Hardware**: Quantum simulations are executed on classical statevector simulators.
- **No Quantum Advantage Claimed**: The quantum algorithm serves as an active-space electronic structure benchmark.
- **Data Integrity**: No empirical PET-Gym metrics or conversion rates were fabricated.

## 9. Reproducibility Metadata

- **Random Seed**: `42`
- **Configuration Hash**: `870fb4b9`
- **Pipeline Version**: `0.1.0`
- **Run Artifacts Root**: `runs\run_20261007_160419_870fb4b9`
