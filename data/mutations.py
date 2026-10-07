"""Robust mutation parsing, validation, and sequence manipulation for PETase variants."""

from dataclasses import dataclass
import re
from typing import List, Optional, Set, Tuple

# Standard 20 canonical amino acids
CANONICAL_AMINO_ACIDS: Set[str] = set("ACDEFGHIKLMNPQRSTVWY")

# 3-letter to 1-letter amino acid mapping
THREE_TO_ONE_AA = {
    "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E",
    "PHE": "F", "GLY": "G", "HIS": "H", "ILE": "I",
    "LYS": "K", "LEU": "L", "MET": "M", "ASN": "N",
    "PRO": "P", "GLN": "Q", "ARG": "R", "SER": "S",
    "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
    "SEC": "U", "PYL": "O"
}

# Regex for single-letter mutation (e.g. S160A, S-160-A, p.S160A)
_MUTATION_REGEX_1L = re.compile(r"^(?:p\.)?([A-Za-z])[-_]?(\d+)[-_]?([A-Za-z*])$")
# Regex for three-letter mutation (e.g. Ser160Ala, p.Ser160Ala)
_MUTATION_REGEX_3L = re.compile(
    r"^(?:p\.)?([A-Za-z]{3})[-_]?(\d+)[-_]?([A-Za-z]{3}|\*|Ter|Stop)$", re.IGNORECASE
)


class MutationParseError(ValueError):
    """Raised when mutation string syntax or amino acid symbol is invalid."""
    pass


class SequenceMismatchError(ValueError):
    """Raised when wild-type residue in mutation does not match reference sequence."""
    pass


@dataclass(frozen=True, order=True)
class SingleMutation:
    """Represents an individual point mutation at a 1-indexed position."""
    position: int
    from_residue: str
    to_residue: str

    def __post_init__(self):
        if self.position < 1:
            raise MutationParseError(f"Position must be >= 1, got {self.position}")
        if self.from_residue not in CANONICAL_AMINO_ACIDS:
            raise MutationParseError(
                f"Invalid from_residue '{self.from_residue}'. Must be one of {sorted(CANONICAL_AMINO_ACIDS)}"
            )
        if self.to_residue not in CANONICAL_AMINO_ACIDS and self.to_residue != "*":
            raise MutationParseError(
                f"Invalid to_residue '{self.to_residue}'. Must be one of {sorted(CANONICAL_AMINO_ACIDS)}"
            )

    @property
    def is_silent(self) -> bool:
        """Return True if original and mutated residues are identical."""
        return self.from_residue == self.to_residue

    def to_string(self) -> str:
        """Format as canonical single-letter mutation: e.g. S160A."""
        return f"{self.from_residue}{self.position}{self.to_residue}"

    def __str__(self) -> str:
        return self.to_string()


def parse_single_mutation(mutation_str: str) -> SingleMutation:
    """Parse a single mutation substring (e.g., 'S160A', 'Ser160Ala', 'p.S160A').

    Args:
        mutation_str: Raw single mutation string.

    Returns:
        SingleMutation object.

    Raises:
        MutationParseError: If formatting or amino acid codes are invalid.
    """
    cleaned = mutation_str.strip()
    if not cleaned:
        raise MutationParseError("Empty mutation string provided.")

    # Try single letter regex
    match_1l = _MUTATION_REGEX_1L.match(cleaned)
    if match_1l:
        from_res, pos_str, to_res = match_1l.groups()
        from_res = from_res.upper()
        to_res = to_res.upper()
        pos = int(pos_str)
        return SingleMutation(position=pos, from_residue=from_res, to_residue=to_res)

    # Try 3-letter regex
    match_3l = _MUTATION_REGEX_3L.match(cleaned)
    if match_3l:
        from_res_3, pos_str, to_res_3 = match_3l.groups()
        from_res_3 = from_res_3.upper()
        to_res_3 = to_res_3.upper()
        pos = int(pos_str)

        if from_res_3 not in THREE_TO_ONE_AA:
            raise MutationParseError(f"Unknown 3-letter amino acid: '{from_res_3}'")
        from_res = THREE_TO_ONE_AA[from_res_3]

        if to_res_3 in ("*", "TER", "STOP"):
            to_res = "*"
        elif to_res_3 in THREE_TO_ONE_AA:
            to_res = THREE_TO_ONE_AA[to_res_3]
        else:
            raise MutationParseError(f"Unknown 3-letter target amino acid: '{to_res_3}'")

        return SingleMutation(position=pos, from_residue=from_res, to_residue=to_res)

    raise MutationParseError(f"Cannot parse mutation syntax: '{mutation_str}'")


def parse_mutations(mutations_str: Optional[str]) -> List[SingleMutation]:
    """Parse multi-mutant strings separated by semicolon, colon, slash, space, comma, or plus.

    Accepts 'WT', 'wildtype', 'none', '', '-', etc. as wild-type (returns empty list).

    Args:
        mutations_str: Mutation string containing one or more mutations.

    Returns:
        List of SingleMutation objects sorted by position.

    Raises:
        MutationParseError: If syntax is invalid or duplicate contradictory positions exist.
    """
    if mutations_str is None:
        return []

    cleaned = str(mutations_str).strip()
    if not cleaned or cleaned.lower() in ("wt", "wildtype", "wild-type", "wild_type", "none", "-", "nan", "null"):
        return []

    # Split by standard delimiters: ;, :, /, +, comma, or whitespace
    tokens = [t.strip() for t in re.split(r"[,;:\s\+/]+", cleaned) if t.strip()]

    parsed_list: List[SingleMutation] = []
    seen_positions: Set[int] = set()

    for tok in tokens:
        mut = parse_single_mutation(tok)
        if mut.position in seen_positions:
            raise MutationParseError(
                f"Conflicting multiple mutations at position {mut.position} in '{mutations_str}'"
            )
        seen_positions.add(mut.position)
        parsed_list.append(mut)

    # Return sorted by sequence position for canonical ordering
    return sorted(parsed_list, key=lambda m: m.position)


def normalize_mutation_string(mutations_str: Optional[str]) -> str:
    """Convert any supported mutation representation into canonical format 'S160A;D206G' or 'WT'.

    Args:
        mutations_str: Raw mutation string.

    Returns:
        Canonical mutation string.
    """
    muts = parse_mutations(mutations_str)
    if not muts:
        return "WT"
    return ";".join(m.to_string() for m in muts)


def apply_mutations_to_sequence(
    parent_sequence: str,
    mutations: List[SingleMutation] | str,
    offset: int = 1,
    strict_wt_check: bool = True
) -> str:
    """Apply parsed or raw mutations to a reference sequence (1-indexed with optional offset).

    Args:
        parent_sequence: Amino acid sequence string.
        mutations: List of SingleMutation objects or mutation string.
        offset: Numbering offset (default 1 means sequence index 0 corresponds to residue 1).
        strict_wt_check: If True, verify from_residue matches reference sequence.

    Returns:
        Mutated amino acid sequence.

    Raises:
        SequenceMismatchError: If WT residue does not match or position is out of bounds.
    """
    if isinstance(mutations, str):
        parsed = parse_mutations(mutations)
    else:
        parsed = mutations

    seq_chars = list(parent_sequence.strip().upper())
    seq_len = len(seq_chars)

    for mut in parsed:
        idx = (mut.position - offset)
        if idx < 0 or idx >= seq_len:
            raise SequenceMismatchError(
                f"Mutation position {mut.position} is out of bounds for sequence length {seq_len} (offset={offset})"
            )
        expected_wt = seq_chars[idx]
        if strict_wt_check and expected_wt != mut.from_residue:
            raise SequenceMismatchError(
                f"Reference residue mismatch at position {mut.position}: expected '{expected_wt}', but mutation specifies '{mut.from_residue}'"
            )
        seq_chars[idx] = mut.to_residue

    return "".join(seq_chars)


def extract_mutations_from_sequences(
    parent_sequence: str,
    mutant_sequence: str,
    offset: int = 1
) -> List[SingleMutation]:
    """Compare parent and mutant sequence to derive single point mutations.

    Args:
        parent_sequence: Wild-type amino acid sequence.
        mutant_sequence: Variant amino acid sequence.
        offset: 1-indexed residue numbering offset.

    Returns:
        List of SingleMutation objects.
    """
    p_seq = parent_sequence.strip().upper()
    m_seq = mutant_sequence.strip().upper()

    if len(p_seq) != len(m_seq):
        raise ValueError(f"Sequences must have equal length, got {len(p_seq)} and {len(m_seq)}")

    muts: List[SingleMutation] = []
    for i, (p_res, m_res) in enumerate(zip(p_seq, m_seq)):
        if p_res != m_res:
            pos = i + offset
            muts.append(SingleMutation(position=pos, from_residue=p_res, to_residue=m_res))

    return muts
