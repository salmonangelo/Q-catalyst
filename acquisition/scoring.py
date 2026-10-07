"""Acquisition scoring functions and chemistry cost proxy models."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from acquisition.config import AcquisitionConfig, AcquisitionWeights
from data.mutations import parse_mutations


@dataclass(frozen=True)
class CandidateSubScores:
    """Individual normalized sub-scores contributing to final acquisition priority."""
    norm_performance: float
    norm_uncertainty: float
    norm_proximity: float
    norm_diversity: float
    norm_cost_proxy: float
    final_acquisition_score: float
    active_strategy: str


def compute_chemistry_cost_proxy(mutations_str: str, has_structure_mapping: bool = True) -> float:
    """Compute lightweight proxy cost for downstream chemistry modeling.

    NOTE: Explicitly designated as a 'proxy' metric based on cluster mutational complexity.
    Actual quantum/DFT runtime data will supersede this in subsequent phases.

    Args:
        mutations_str: Mutation string.
        has_structure_mapping: Whether candidate is mapped to reference PDB.

    Returns:
        Proxy cost score (higher = more computationally demanding cluster).
    """
    try:
        muts = parse_mutations(mutations_str)
        n_muts = len(muts)
    except Exception:
        n_muts = 1

    base_cost = 1.0
    mutation_overhead = n_muts * 0.5
    mapping_overhead = 0.0 if has_structure_mapping else 1.0

    return float(base_cost + mutation_overhead + mapping_overhead)


class AcquisitionScorer:
    """Calculates normalized multi-objective acquisition priority scores."""

    def __init__(self, config: Optional[AcquisitionConfig] = None):
        self.config = config or AcquisitionConfig()
        self.weights = self.config.weights

    def score_candidates(
        self,
        performance_scores: np.ndarray,
        uncertainty_scores: Optional[np.ndarray],
        proximity_scores: Optional[np.ndarray],
        diversity_scores: np.ndarray,
        mutations_list: List[str],
        has_structure_mapping: Optional[List[bool]] = None,
        strategy_override: Optional[str] = None,
        gate0_validated: bool = False,
    ) -> Tuple[np.ndarray, List[CandidateSubScores], str]:
        """Compute composite acquisition score vector for a candidate pool.

        Args:
            performance_scores: Raw predicted activity/fitness values (N,).
            uncertainty_scores: Normalized uncertainty scores (N,) or None.
            proximity_scores: Proximity decay scores (N,) or None (NaNs allowed).
            diversity_scores: Dynamic diversity scores (N,).
            mutations_list: List of mutation strings.
            has_structure_mapping: Boolean flags for structure mapping availability.
            strategy_override: Optional manual strategy override.
            gate0_validated: Whether Gate 0 verified that uncertainty correlates with error.

        Returns:
            Tuple of (final_scores_array: np.ndarray, list_of_subscores: List, active_strategy_name: str).
        """
        n = len(performance_scores)
        if n == 0:
            return np.array([], dtype=np.float32), [], "empty"

        # 1. Determine active strategy (handling Gate-0 fallback)
        strategy = strategy_override or self.config.strategy

        if strategy == "mechanism_aware" and self.config.require_gate0_validation and not gate0_validated:
            strategy = "mechanism_aware_without_uncertainty"

        # 2. Normalize performance into [0, 1]
        perf = np.asarray(performance_scores, dtype=float)
        p_min, p_max = np.nanmin(perf), np.nanmax(perf)
        if p_max > p_min:
            norm_perf = np.clip((perf - p_min) / (p_max - p_min), 0.0, 1.0)
        else:
            norm_perf = np.ones(n, dtype=float)

        # 3. Normalize uncertainty into [0, 1]
        if uncertainty_scores is not None and strategy in ("mechanism_aware", "uncertainty_only"):
            unc = np.asarray(uncertainty_scores, dtype=float)
            u_min, u_max = np.nanmin(unc), np.nanmax(unc)
            if u_max > u_min:
                norm_unc = np.clip((unc - u_min) / (u_max - u_min), 0.0, 1.0)
            else:
                norm_unc = np.ones(n, dtype=float)
        else:
            norm_unc = np.zeros(n, dtype=float)

        # 4. Proximity scores (already in [0, 1], replace NaNs with neutral 0.50 fallback)
        if proximity_scores is not None and strategy in ("mechanism_aware", "mechanism_aware_without_uncertainty"):
            prox = np.asarray(proximity_scores, dtype=float)
            norm_prox = np.where(np.isnan(prox), 0.50, np.clip(prox, 0.0, 1.0))
        else:
            norm_prox = np.zeros(n, dtype=float)

        # 5. Diversity scores (already in [0, 1])
        norm_div = np.clip(np.asarray(diversity_scores, dtype=float), 0.0, 1.0)

        # 6. Chemistry Cost Proxy
        mapping_flags = has_structure_mapping or [True] * n
        raw_costs = np.array([
            compute_chemistry_cost_proxy(m, mapping_flags[i])
            for i, m in enumerate(mutations_list)
        ])
        c_min, c_max = np.min(raw_costs), np.max(raw_costs)
        if c_max > c_min:
            norm_cost = np.clip((raw_costs - c_min) / (c_max - c_min), 0.0, 1.0)
        else:
            norm_cost = np.zeros(n, dtype=float)

        # 7. Strategy-specific score computation
        w = self.weights

        if strategy == "performance_only":
            final_scores = norm_perf.copy()

        elif strategy == "uncertainty_only":
            final_scores = norm_unc.copy()

        elif strategy == "mechanism_aware_without_uncertainty":
            # Re-normalize weights excluding uncertainty
            tot_w = w.alpha_performance + w.gamma_proximity + w.delta_diversity + w.lambda_cost
            a = w.alpha_performance / tot_w
            g = w.gamma_proximity / tot_w
            d = w.delta_diversity / tot_w
            l = w.lambda_cost / tot_w

            final_scores = (a * norm_perf) + (g * norm_prox) + (d * norm_div) - (l * norm_cost)

        else:  # mechanism_aware
            tot_w = w.alpha_performance + w.beta_uncertainty + w.gamma_proximity + w.delta_diversity + w.lambda_cost
            a = w.alpha_performance / tot_w
            b = w.beta_uncertainty / tot_w
            g = w.gamma_proximity / tot_w
            d = w.delta_diversity / tot_w
            l = w.lambda_cost / tot_w

            final_scores = (a * norm_perf) + (b * norm_unc) + (g * norm_prox) + (d * norm_div) - (l * norm_cost)

        subscores_list = []
        for i in range(n):
            subscores_list.append(
                CandidateSubScores(
                    norm_performance=float(norm_perf[i]),
                    norm_uncertainty=float(norm_unc[i]),
                    norm_proximity=float(norm_prox[i]),
                    norm_diversity=float(norm_div[i]),
                    norm_cost_proxy=float(norm_cost[i]),
                    final_acquisition_score=float(final_scores[i]),
                    active_strategy=strategy,
                )
            )

        return final_scores.astype(np.float32), subscores_list, strategy
