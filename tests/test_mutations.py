"""Unit tests for mutation parsing, validation, and sequence manipulation."""

import pytest
from data.mutations import (
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


def test_parse_single_mutation_1letter():
    m = parse_single_mutation("S160A")
    assert m.position == 160
    assert m.from_residue == "S"
    assert m.to_residue == "A"
    assert m.to_string() == "S160A"


def test_parse_single_mutation_3letter():
    m = parse_single_mutation("Ser160Ala")
    assert m.position == 160
    assert m.from_residue == "S"
    assert m.to_residue == "A"

    m_prefix = parse_single_mutation("p.Asp206Gly")
    assert m_prefix.position == 206
    assert m_prefix.from_residue == "D"
    assert m_prefix.to_residue == "G"


def test_parse_multiple_mutations_delimiters():
    # Semicolon
    muts1 = parse_mutations("S160A;D206G")
    assert len(muts1) == 2
    assert [m.to_string() for m in muts1] == ["S160A", "D206G"]

    # Colon
    muts2 = parse_mutations("S160A:D206G")
    assert [m.to_string() for m in muts2] == ["S160A", "D206G"]

    # Slash
    muts3 = parse_mutations("S160A/D206G")
    assert [m.to_string() for m in muts3] == ["S160A", "D206G"]

    # Comma and space
    muts4 = parse_mutations("S160A, D206G, H237A")
    assert len(muts4) == 3
    assert [m.to_string() for m in muts4] == ["S160A", "D206G", "H237A"]


def test_parse_mutations_sorting():
    # Input out of numerical order should be sorted
    muts = parse_mutations("H237A;S160A;D206G")
    assert [m.to_string() for m in muts] == ["S160A", "D206G", "H237A"]


def test_wildtype_handling():
    assert parse_mutations("WT") == []
    assert parse_mutations("wt") == []
    assert parse_mutations("WildType") == []
    assert parse_mutations("none") == []
    assert parse_mutations("-") == []
    assert parse_mutations("") == []
    assert parse_mutations(None) == []
    assert normalize_mutation_string("WT") == "WT"
    assert normalize_mutation_string(None) == "WT"


def test_normalize_mutation_string():
    assert normalize_mutation_string("D206G;S160A") == "S160A;D206G"
    assert normalize_mutation_string("Ser160Ala:Asp206Gly") == "S160A;D206G"


def test_parse_invalid_mutations():
    # Invalid amino acid symbol 'Z'
    with pytest.raises(MutationParseError):
        parse_single_mutation("S160Z")

    # Invalid position 0
    with pytest.raises(MutationParseError):
        parse_single_mutation("S0A")

    # Corrupt format
    with pytest.raises(MutationParseError):
        parse_single_mutation("NOT_A_MUTATION")

    # Conflicting mutations at same site
    with pytest.raises(MutationParseError):
        parse_mutations("S160A;S160G")


def test_apply_mutations_to_sequence():
    wt_seq = "MSLEASAGPFTVRS"
    # M1 is pos 1, S2 is pos 2, etc.
    mutated = apply_mutations_to_sequence(wt_seq, "M1A;S2G", offset=1, strict_wt_check=True)
    assert mutated == "AGLEASAGPFTVRS"


def test_apply_mutations_mismatch_error():
    wt_seq = "MSLEASAGPFTVRS"
    # Position 1 is M, but mutation says S1A -> should fail
    with pytest.raises(SequenceMismatchError):
        apply_mutations_to_sequence(wt_seq, "S1A", offset=1, strict_wt_check=True)


def test_apply_mutations_out_of_bounds():
    wt_seq = "MSLE"
    with pytest.raises(SequenceMismatchError):
        apply_mutations_to_sequence(wt_seq, "S10A", offset=1)


def test_extract_mutations_from_sequences():
    seq1 = "ACDEFGHIKL"
    seq2 = "ACAEFGHIKM"  # D3A, L10M
    muts = extract_mutations_from_sequences(seq1, seq2, offset=1)
    assert [m.to_string() for m in muts] == ["D3A", "L10M"]
