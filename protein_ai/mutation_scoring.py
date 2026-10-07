"""ESM Mutation Scoring calculating zero-shot log-likelihood ratios."""

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from data.build_dataset import REFERENCE_PARENT_SEQUENCES
from data.mutations import SingleMutation, parse_mutations
from protein_ai.config import ESMConfig
from protein_ai.esm import ESMModelWrapper, get_esm_model


@dataclass(frozen=True)
class MutationScoreResult:
    """Zero-shot mutation score for a variant."""
    variant_id: str
    mutations: str
    parent_enzyme: str
    model_name: str
    mutation_score: float
    score_type: str = "log_likelihood_difference"


class MutationScorer:
    """Calculates zero-shot masked marginal sequence likelihood scores for single and multi-mutants."""

    def __init__(
        self,
        config: Optional[ESMConfig] = None,
        model_wrapper: Optional[ESMModelWrapper] = None,
        parent_sequences: Optional[Dict[str, str]] = None,
    ):
        self.config = config or ESMConfig()
        self.model = model_wrapper or get_esm_model(self.config)
        self.parent_sequences = parent_sequences or REFERENCE_PARENT_SEQUENCES

    def score_variant(
        self,
        variant_id: str,
        mutations_str: str,
        parent_enzyme: str = "IsPETase",
        parent_sequence: Optional[str] = None,
    ) -> MutationScoreResult:
        """Compute zero-shot mutation score for a variant.

        Args:
            variant_id: Unique identifier.
            mutations_str: Canonical mutation string (e.g. S160A;D206G or WT).
            parent_enzyme: Name of parent enzyme.
            parent_sequence: Optional reference wild-type sequence.

        Returns:
            MutationScoreResult instance.
        """
        ref_seq = parent_sequence or self.parent_sequences.get(parent_enzyme)
        if not ref_seq:
            raise ValueError(f"No reference sequence available for parent enzyme '{parent_enzyme}'.")

        parsed_muts = parse_mutations(mutations_str)
        if not parsed_muts:
            # WT variant has zero log-likelihood difference relative to itself
            return MutationScoreResult(
                variant_id=variant_id,
                mutations="WT",
                parent_enzyme=parent_enzyme,
                model_name=self.model.model_name,
                mutation_score=0.0,
                score_type="log_likelihood_difference",
            )

        total_score = 0.0
        for mut in parsed_muts:
            delta_ll = self.model.compute_mutation_log_likelihood(
                parent_sequence=ref_seq,
                pos_1indexed=mut.position,
                wildtype_aa=mut.from_residue,
                mutant_aa=mut.to_residue,
            )
            total_score += delta_ll

        return MutationScoreResult(
            variant_id=variant_id,
            mutations=";".join(m.to_string() for m in parsed_muts),
            parent_enzyme=parent_enzyme,
            model_name=self.model.model_name,
            mutation_score=float(total_score),
            score_type="log_likelihood_difference",
        )

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Score all variants in a DataFrame."""
        results = []
        for _, row in df.iterrows():
            var_id = str(row.get("variant_id", ""))
            muts = str(row.get("mutations", "WT"))
            parent = str(row.get("parent_enzyme", "IsPETase"))

            score_res = self.score_variant(
                variant_id=var_id,
                mutations_str=muts,
                parent_enzyme=parent,
            )
            results.append({
                "variant_id": score_res.variant_id,
                "mutations": score_res.mutations,
                "parent_enzyme": score_res.parent_enzyme,
                "model_name": score_res.model_name,
                "mutation_score": score_res.mutation_score,
                "score_type": score_res.score_type,
            })

        return pd.DataFrame(results)
