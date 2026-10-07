"""Q-Catalyst Phase 4: Classical Chemistry Layer.

Provides active-site extraction, reduced cluster modeling, mutation mapping,
geometry validation, classical electronic structure (HF/DFT), mechanistic descriptors,
and data contracts for downstream quantum simulations.
"""

from chemistry.active_site import ActiveSiteExtractor, ActiveSiteReport
from chemistry.cluster import ClusterAtom, ClusterBuilder, ReducedCluster
from chemistry.config import ChemistryConfig, ClusterConfig, ElectronicStructureConfig
from chemistry.descriptors import DescriptorExtractor, MechanisticDescriptors
from chemistry.electronic_structure import (
    ElectronicStructureEngine,
    ElectronicStructureResult,
    PYSCF_AVAILABLE,
)
from chemistry.geometry import GeometryValidationResult, GeometryValidator
from chemistry.mutation import (
    MutationClusterEngine,
    MutationClusterMapping,
    VariantClusterResult,
)
from chemistry.outputs import CHEMISTRY_SCHEMA_COLUMNS, ChemistryOutputWriter
from chemistry.structure import AtomCoord, ResidueAtoms, StructureReader

__all__ = [
    "ActiveSiteExtractor",
    "ActiveSiteReport",
    "AtomCoord",
    "ChemistryConfig",
    "ChemistryOutputWriter",
    "CHEMISTRY_SCHEMA_COLUMNS",
    "ClusterAtom",
    "ClusterBuilder",
    "ClusterConfig",
    "DescriptorExtractor",
    "ElectronicStructureConfig",
    "ElectronicStructureEngine",
    "ElectronicStructureResult",
    "GeometryValidationResult",
    "GeometryValidator",
    "MechanisticDescriptors",
    "MutationClusterEngine",
    "MutationClusterMapping",
    "PYSCF_AVAILABLE",
    "ReducedCluster",
    "ResidueAtoms",
    "StructureReader",
    "VariantClusterResult",
]
