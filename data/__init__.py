"""Q-Catalyst Data Engineering Package."""

from .contracts import FILE_CONTRACTS, FileContract, verify_contract
from .mutations import (
    CANONICAL_AMINO_ACIDS,
    MutationParseError,
    SequenceMismatchError,
    SingleMutation,
    apply_mutations_to_sequence,
    extract_mutations_from_sequences,
    normalize_mutation_string,
    parse_mutations,
    parse_single_mutation,
)
from .schema import (
    CANONICAL_COLUMNS,
    COLUMN_DTYPES,
    VariantRecord,
    enforce_canonical_schema,
)
from .split import DatasetSplitter, SplitManifest
from .structure_utils import ResidueInfo, StructureManager, StructureMappingError
from .validate import ValidationIssue, ValidationReport, validate_dataframe, validate_file

__all__ = [
    "CANONICAL_COLUMNS",
    "COLUMN_DTYPES",
    "CANONICAL_AMINO_ACIDS",
    "VariantRecord",
    "enforce_canonical_schema",
    "SingleMutation",
    "MutationParseError",
    "SequenceMismatchError",
    "parse_single_mutation",
    "parse_mutations",
    "normalize_mutation_string",
    "apply_mutations_to_sequence",
    "extract_mutations_from_sequences",
    "ValidationIssue",
    "ValidationReport",
    "validate_dataframe",
    "validate_file",
    "DatasetSplitter",
    "SplitManifest",
    "ResidueInfo",
    "StructureManager",
    "StructureMappingError",
    "FILE_CONTRACTS",
    "FileContract",
    "verify_contract",
]
