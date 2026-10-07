# Q-Catalyst Phase 4: Classical Chemistry Layer

## Overview
Phase 4 implements the **Classical Chemistry Layer** of the Q-Catalyst triage pipeline. It ingests high-priority candidate variants selected by the Phase 3 Smart Acquisition Gate (`acquisition/selected_candidates.parquet`), extracts a scientifically traceable **reduced active-site cluster** from the crystallographic structure of *Ideonella sakaiensis* PETase (PDB `5XJH`), performs mutation mapping and local geometry adaptation, executes classical electronic-structure calculations (Hartree-Fock and optional DFT), and extracts mechanistic descriptors for downstream quantum simulations.

---

## Scientific Methodology & Rationale

### 1. Why a Reduced Cluster?
Simulating an entire enzyme (~290 residues, >4,500 atoms) with quantum-mechanical electronic structure methods is computationally intractable. A **reduced active-site cluster model** isolates the immediate catalytic center where ester bond cleavage occurs, capturing local orbital energies, dipole moments, and electrostatic potentials while maintaining computational feasibility for high-throughput triage.

### 2. Active-Site Residues (PDB 5XJH)
The initial catalytic region is defined by key functional residues:
- **Catalytic Triad**: `Ser160` (nucleophile), `Asp206` (acid/base), `His237` (general base).
- **Oxyanion Hole**: `Tyr87`, `Met161` (stabilizes tetrahedral intermediate oxyanion).
- **Substrate Cleft**: `Trp185`, `Trp159` (aromatic $\pi$-stacking with terephthalate rings).

> **Important**: These residues define the reduced active-site cluster for this MVP. They do NOT claim to represent the entire dynamic catalytic machinery or long-range allosteric conformational changes of PETase.

### 3. Mutation Mapping & Provenance
For each candidate:
- **Inside Cluster**: If a mutation occurs at an active-site residue (e.g. `S160A`), a model-generated local geometry is constructed, and tagged explicitly as `geometry_source = "model_generated_from_5XJH"`.
- **Outside Cluster**: If a mutation is distal to the active site (e.g. `R280A`), the local catalytic cluster geometry is unperturbed, recorded with `mutation_cluster_relation = "outside_cluster"`.

### 4. Geometry Validation
Before any electronic-structure calculations, geometries are screened:
- Detection of `NaN` or `Inf` coordinates.
- Steric clash detection (minimum interatomic distance $< 0.50\text{ \AA}$).
- Elemental symbol validation.
- Output: `geometry_status` (`"valid"`, `"warning"`, or `"invalid"`).

### 5. Classical Electronic Structure & Descriptors
- **Method**: Hartree-Fock (`HF` baseline) and optional DFT (`B3LYP`).
- **Charge & Multiplicity**: Explicitly configured (default `charge = 0`, `multiplicity = 1`).
- **Descriptors Extracted**:
  - Total electronic energy $E_{\text{variant}}$ (Hartree)
  - Wild-type reference energy $E_{\text{ref}}$ (Hartree)
  - Relative energy difference $\Delta E = E_{\text{variant}} - E_{\text{ref}}$
  - Dipole moment vector ($\mu_x, \mu_y, \mu_z$) and magnitude $|\vec{\mu}|$ (Debye)
  - Frontier orbital energies ($E_{\text{HOMO}}$, $E_{\text{LUMO}}$, and HOMO-LUMO gap $\Delta \epsilon$)
  - Catalytic triad inter-residue distances (`Ser160-His237`, `His237-Asp206`)
- **SCF Convergence**: Recorded explicitly (`scf_converged`, `scf_iterations`, `failure_reason`).

### 6. Deterministic Caching
All calculations are hashed by `(cluster_id, geometry_hash, method, basis, charge, multiplicity)` and cached under `artifacts/chemistry/cache/` to eliminate redundant expensive evaluations.

---

## File Contracts & Outputs

1. **`chemistry/chem_results.parquet`**: Master chemistry results table conforming to the canonical schema.
2. **`chemistry/active_site_report.json`**: Structural validation report for PDB 5XJH active-site residues.
3. **`chemistry/clusters/cluster_manifest.json`**: Machine-readable manifest of all extracted clusters.
4. **`chemistry/clusters/*.xyz`**: Cartesian coordinate files for WT and variant clusters.

---

## Execution Guide

### Standard Evaluation:
```bash
python -m chemistry.evaluate --input acquisition/selected_candidates.parquet --output chemistry/chem_results.parquet
```

### Synthetic Test Fixture Mode:
```bash
python -m chemistry.evaluate --input acquisition/selected_candidates.parquet --test-fixture
```

### Optional DFT Mode:
```bash
python -m chemistry.evaluate --input acquisition/selected_candidates.parquet --run-dft
```
