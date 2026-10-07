"""Configuration schema for Phase 4 Classical Chemistry module."""

from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class ClusterConfig(BaseModel):
    """Configuration for reduced active-site catalytic cluster definition."""
    reference_pdb_path: Path = Path("data/structures/5xjh.pdb")
    reference_chain_id: str = "A"
    reference_parent: str = "IsPETase"
    # Catalytic Triad: Ser160, Asp206, His237
    # Oxyanion Hole: Tyr87, Met161
    # Substrate Pocket: Trp185, Trp159
    active_site_residues: List[int] = Field(
        default_factory=lambda: [160, 206, 237, 87, 161, 185, 159]
    )
    catalytic_center_residue: int = 160  # Ser160 nucleophile
    cluster_radius_angstrom: float = 6.0  # Radius around catalytic center for secondary shell atoms
    include_backbone: bool = True
    hydrogen_addition_method: str = "geometric_idealized"  # Options: 'geometric_idealized', 'none'
    pH: float = 7.0


class ElectronicStructureConfig(BaseModel):
    """Configuration for classical Hartree-Fock and DFT electronic structure calculations."""
    method: str = "HF"  # Options: 'HF', 'RHF', 'UHF', 'DFT', 'B3LYP'
    basis: str = "sto-3g"  # Options: 'sto-3g', '6-31g', 'def2-svp'
    charge: int = 0  # Net charge of reduced active-site cluster
    spin_multiplicity: int = 1  # 2S + 1 (1 = singlet)
    max_scf_cycles: int = 100
    conv_tol: float = 1e-7  # Energy convergence tolerance in Hartree
    run_dft: bool = False
    dft_xc: str = "b3lyp"
    dft_basis: str = "sto-3g"


class ChemistryConfig(BaseModel):
    """Unified configuration for Classical Chemistry Layer."""
    cluster: ClusterConfig = Field(default_factory=ClusterConfig)
    electronic_structure: ElectronicStructureConfig = Field(default_factory=ElectronicStructureConfig)

    cache_dir: Path = Path("artifacts/chemistry/cache")
    clusters_dir: Path = Path("chemistry/clusters")
    output_results_parquet: Path = Path("chemistry/chem_results.parquet")
    output_active_site_report: Path = Path("chemistry/active_site_report.json")
    output_cluster_manifest: Path = Path("chemistry/clusters/cluster_manifest.json")
