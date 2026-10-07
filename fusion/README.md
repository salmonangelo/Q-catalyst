# Phase 6: Multimodal Evidence Fusion & Candidate Decision Engine

## 1. Scientific Overview & Purpose

The **Q-Catalyst Evidence Fusion Engine** converts disparate computational predictions across Sequence AI, Uncertainty Estimation, Structural Mechanism, Classical Electronic Structure, and Active-Space Quantum Simulation into a single, transparent, and reproducible **Candidate Triage Profile**.

> **CRITICAL SCIENTIFIC GUARDRAIL**:
> This engine is a **computational triage and candidate prioritization system**. It does **NOT** measure, prove, or guarantee wet-lab enzyme activity, PET degradation rates, or biological kinetics. Its purpose is to answer:
> *"Given all currently available in-silico evidence, which engineered PETase variants warrant laboratory investigation and synthesis, and why?"*

---

## 2. Multimodal Evidence Channels

The engine aggregates evidence from 6 independent channels, normalizing each into a documented $[0, 1]$ scale:

| Evidence Channel | Upstream Module | Primary Signal | Normalization Method | Quality / Provenance Retained |
| :--- | :--- | :--- | :--- | :--- |
| **Protein-AI Fitness** | Phase 2 (`protein_ai/`) | ESM / Zero-shot sequence fitness | Min-max or sigmoid scaling of model prediction | Synthetic vs empirical source flag |
| **Uncertainty Quality** | Phase 2 (`uncertainty/`) | Ensemble standard deviation / conformal spread | $S_{\text{unc}} = 1.0 - \text{clip}(\sigma / \sigma_{\max}, 0, 1)$ | Flagged as `LOW`, `MEDIUM`, `HIGH`, `UNKNOWN` |
| **Mechanism Proximity** | Phase 3 (`acquisition/`) | Structural proximity to catalytic triad (S160, D206, H237) | Exponential decay: $e^{-d / d_0}$ ($d_0 = 8.0\,\text{Å}$) | Exact minimum Ångström distance preserved |
| **Classical Chemistry** | Phase 4 (`chemistry/`) | Active-site cluster geometry validity & HF SCF convergence | Binary validity + energy stability penalty | `CLASSICAL_FALLBACK` vs PySCF provenance |
| **Quantum Agreement** | Phase 5 (`quantum/`) | Active-space (4e, 4o) VQE vs CASCI variational error | $S_{\text{qm}} = e^{-|\Delta E_{\text{VQE}-\text{CASCI}}| / \epsilon_0}$ ($\epsilon_0 = 0.05\,\text{Ha}$) | Backend explicitly labeled `SIMULATOR` |
| **Sequence Diversity** | Phase 3 (`acquisition/`) | Mutational novelty across candidate batch | Min-max normalization of sequence distance | Batch diversity relative score |

---

## 3. Transparent Composite Scoring Formula

The composite decision score $F_i$ for candidate $i$ is calculated as a weighted linear combination:

$$F_i = w_{\text{ai}} S_{\text{ai}} + w_{\text{unc}} S_{\text{unc}} + w_{\text{mech}} S_{\text{mech}} + w_{\text{chem}} S_{\text{chem}} + w_{\text{qm}} S_{\text{qm}} + w_{\text{div}} S_{\text{div}}$$

### Default Weight Profile (Configurable in `configs/config.yaml`):
- $w_{\text{ai}} = 0.25$ (Protein-AI Sequence Fitness)
- $w_{\text{unc}} = 0.15$ (Prediction Uncertainty Quality)
- $w_{\text{mech}} = 0.20$ (Active-Site Proximity)
- $w_{\text{chem}} = 0.15$ (Classical Chemistry Feasibility)
- $w_{\text{qm}} = 0.15$ (Reduced Active-Space Quantum Agreement)
- $w_{\text{div}} = 0.10$ (Candidate Batch Diversity)
- **Constraint**: $\sum w_k = 1.0$ (strictly validated via Pydantic schema).

---

## 4. Missing-Evidence & Data-Quality Policies

### Missing Evidence Policy (`renormalize_available`)
Missing evidence is **never silently converted to zero**. The engine calculates:
- **Evidence Coverage Score**: $C_i = \frac{N_{\text{available}}}{6}$
- When channels are uncomputed (e.g. quantum simulation not run for lower-priority candidates), weights are dynamically renormalized over the subset of available channels:
$$w_k' = \frac{w_k}{\sum_{j \in \text{Available}} w_j}$$

### Synthetic Data Policy (`preserve_provenance`)
When benchmarking datasets (e.g. local PET-Gym files) are absent, test fixtures retain explicit provenance tags:
- `data_quality_flag = "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA"`
- `data_source = "synthetic_test_fixture"`

---

## 5. Decision Tiers & Confidence Logic

Candidates are categorized into transparent triage tiers using configurable threshold boundaries:

1. **`PRIORITIZE`**:
   - Composite score $F_i \ge 0.70$
   - Evidence coverage $C_i \ge 0.60$
   - Uncertainty flag $\ne \text{HIGH}$
2. **`PROMISING_BUT_UNCERTAIN`**:
   - Composite score $F_i \ge 0.50$
3. **`INSUFFICIENT_EVIDENCE`**:
   - Evidence coverage $C_i < 0.40$
4. **`LOW_PRIORITY`**:
   - Composite score $F_i < 0.50$

### Confidence Labeling
- **`HIGH_CONFIDENCE`**: Evidence coverage $\ge 80\%$ and `LOW` predictive uncertainty.
- **`MODERATE_CONFIDENCE`**: Evidence coverage $\ge 50\%$ and `LOW` or `MEDIUM` uncertainty.
- **`LOW_CONFIDENCE`**: Sparse evidence coverage or `HIGH` uncertainty.

---

## 6. Deterministic Explainability Engine

For every candidate, the system generates rule-based natural language summaries, positive factors, negative factors, missing evidence lists, and scientific limitations without probabilistic LLM hallucination:

```json
{
  "candidate_id": "VAR_001",
  "rank": 1,
  "decision_status": "PRIORITIZE",
  "confidence_label": "HIGH_CONFIDENCE",
  "fusion_score": 0.8425,
  "summary": "Ranked #1 with composite fusion score 0.84 (PRIORITIZE). Supported by strong protein sequence fitness score (0.88), high catalytic active-site geometric proximity (0.92). Evidence coverage: 6/6 channels.",
  "positive_factors": [
    "Strong protein sequence fitness score (0.88).",
    "Low predictive uncertainty (LOW).",
    "High catalytic active-site geometric proximity (0.92).",
    "Valid active-site cluster geometry and converged classical electronic structure.",
    "Excellent VQE/CASCI quantum agreement (|ΔE| = 0.0093 Ha)."
  ],
  "negative_factors": [],
  "missing_evidence": [],
  "limitations": [
    "This ranking represents computational triage recommendation, not experimental proof of enzyme kinetics.",
    "Quantum evidence is derived from classical statevector simulation of a reduced (4e, 4o) active-space model.",
    "Active-space integrals were derived from physical-chemical model calculations rather than ab-initio PySCF."
  ]
}
```

---

## 7. Artifact Schema & Contracts

Phase 6 produces 4 primary artifacts:
1. `fusion/fusion_results.parquet`: Main candidate triage ranking table.
2. `fusion/evidence_matrix.parquet`: Granular provenance and normalization audit matrix.
3. `fusion/fusion_manifest.json`: Execution metadata, guardrails, and triage distribution.
4. `fusion/candidate_explanations.json`: Machine-readable natural-language explanations.

---

## 8. CLI Execution

To run the complete evidence fusion pipeline:

```bash
python -m fusion.evaluate
```
