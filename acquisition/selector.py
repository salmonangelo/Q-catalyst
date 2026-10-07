"""Budget-constrained, diversity-aware greedy candidate selector and explainer."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from acquisition.config import AcquisitionConfig
from acquisition.diversity import DiversityCalculator
from acquisition.filters import PerformanceFilter
from acquisition.proximity import ActiveSiteProximityCalculator, ProximityResult
from acquisition.scoring import AcquisitionScorer, CandidateSubScores, compute_chemistry_cost_proxy


@dataclass
class SelectedCandidate:
    """Represents a finalized candidate selected for downstream quantum/DFT chemistry."""
    variant_id: str
    parent_enzyme: str
    mutations: str
    predicted_performance: float
    uncertainty: Optional[float]
    proximity_score: Optional[float]
    diversity_score: float
    estimated_chemistry_cost: str  # 'proxy-low', 'proxy-medium', 'proxy-high'
    acquisition_score: float
    selection_rank: int
    selection_reason: str
    structure_mapping_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_candidate_explanation(
    rank: int,
    subscores: CandidateSubScores,
    prox_res: ProximityResult,
    perf_raw: float,
    strategy: str,
) -> str:
    """Generate a factual, human-readable rationale for candidate selection."""
    reasons = []

    # 1. Performance rationale
    if subscores.norm_performance >= 0.75:
        reasons.append(f"high predicted activity ({perf_raw:.2f})")
    elif subscores.norm_performance >= 0.40:
        reasons.append(f"moderate predicted activity ({perf_raw:.2f})")
    else:
        reasons.append(f"baseline activity ({perf_raw:.2f})")

    # 2. Uncertainty rationale
    if "without_uncertainty" not in strategy and subscores.norm_uncertainty > 0.0:
        if subscores.norm_uncertainty >= 0.60:
            reasons.append(f"high model uncertainty (normalized={subscores.norm_uncertainty:.2f})")
        elif subscores.norm_uncertainty >= 0.30:
            reasons.append(f"moderate model uncertainty (normalized={subscores.norm_uncertainty:.2f})")

    # 3. Proximity rationale
    if prox_res.structure_mapping_status in ("mapped", "mapped_wt"):
        if prox_res.min_distance_angstrom is not None and prox_res.min_distance_angstrom <= 8.0:
            reasons.append(
                f"close active-site proximity ({prox_res.min_distance_angstrom:.1f} A to pos {prox_res.closest_active_site_residue})"
            )
        elif prox_res.min_distance_angstrom is not None:
            reasons.append(
                f"moderate active-site distance ({prox_res.min_distance_angstrom:.1f} A)"
            )
    else:
        reasons.append(f"structure mapping notice: {prox_res.structure_mapping_status}")

    # 4. Diversity rationale
    if subscores.norm_diversity >= 0.70:
        reasons.append("high sequence diversity relative to previously selected candidates")
    elif subscores.norm_diversity >= 0.30:
        reasons.append("acceptable sequence diversity")

    core_reasons = "; ".join(reasons)
    return f"Rank #{rank} selected via {strategy}: {core_reasons}."


class SmartAcquisitionSelector:
    """Executes iterative greedy multi-objective selection under chemistry budget constraints."""

    def __init__(
        self,
        config: Optional[AcquisitionConfig] = None,
        proximity_calculator: Optional[ActiveSiteProximityCalculator] = None,
    ):
        self.config = config or AcquisitionConfig()
        self.proximity_calculator = proximity_calculator or ActiveSiteProximityCalculator(self.config.proximity)
        self.filter_engine = PerformanceFilter(self.config)
        self.diversity_calculator = DiversityCalculator(self.config.diversity)
        self.scorer = AcquisitionScorer(self.config)

    def select_candidates(
        self,
        df_candidates: pd.DataFrame,
        embeddings: Optional[np.ndarray] = None,
        gate0_validated: bool = False,
    ) -> Tuple[List[SelectedCandidate], Dict[str, Any]]:
        """Select top K candidates for chemistry modeling using iterative diversity-aware greedy policy.

        Args:
            df_candidates: DataFrame containing variant_id, parent_enzyme, mutations, prediction, uncertainty_score, etc.
            embeddings: Optional array of sequence embeddings aligned with df_candidates.
            gate0_validated: Boolean flag indicating if Gate-0 confirmed uncertainty usefulness.

        Returns:
            Tuple of (list_of_SelectedCandidate, selection_summary_metadata).
        """
        budget = self.config.chemistry_budget
        n_input = len(df_candidates)
        if n_input == 0:
            return [], {
                "requested_budget": budget,
                "selected_count": 0,
                "selection_shortfall": budget,
                "active_strategy": self.config.strategy,
            }

        # 1. Apply performance filter
        filtered_df, filter_meta = self.filter_engine.filter_candidates(df_candidates)
        n_filtered = len(filtered_df)

        if n_filtered == 0:
            return [], {
                "requested_budget": budget,
                "selected_count": 0,
                "selection_shortfall": budget,
                "filter_metadata": filter_meta,
                "active_strategy": self.config.strategy,
            }

        filtered_df = filtered_df.reset_index(drop=True)
        filtered_indices = filtered_df.index.tolist()

        # Align embeddings if provided
        filtered_embeddings = None
        if embeddings is not None and len(embeddings) == n_input:
            # Map original indices to filtered indices
            orig_indices = df_candidates.index.get_indexer(filtered_df.index)
            filtered_embeddings = embeddings[orig_indices]

        # 2. Compute active-site structural proximities
        prox_df = self.proximity_calculator.calculate_dataframe_proximity(filtered_df)
        prox_results_map = {}
        for idx, row in filtered_df.iterrows():
            var_id = str(row["variant_id"])
            p_res = self.proximity_calculator.calculate_proximity(
                variant_id=var_id,
                mutations_str=str(row.get("mutations", "WT")),
                parent_enzyme=str(row.get("parent_enzyme", "IsPETase")),
            )
            prox_results_map[idx] = p_res

        proximity_scores = prox_df["proximity_score"].values
        has_structure_mapping = [
            prox_results_map[i].structure_mapping_status in ("mapped", "mapped_wt")
            for i in range(n_filtered)
        ]

        # 3. Compute pairwise similarity matrix for diversity
        mutations_list = filtered_df["mutations"].astype(str).tolist()
        sim_matrix = self.diversity_calculator.compute_similarity_matrix(
            embeddings=filtered_embeddings,
            mutations_list=mutations_list,
        )

        # 4. Iterative Greedy Diversity Selection Loop
        selected_indices: List[int] = []
        selected_candidates: List[SelectedCandidate] = []
        available_indices = set(range(n_filtered))

        target_k = min(budget, n_filtered)

        active_strategy_used = self.config.strategy
        for rank in range(1, target_k + 1):
            # Dynamic diversity vector relative to already selected subset
            diversity_vector = self.diversity_calculator.compute_batch_diversity(
                selected_indices=selected_indices,
                sim_matrix=sim_matrix,
            )

            # Recompute composite acquisition scores
            perf_vals = filtered_df["prediction"].values.astype(float)
            unc_vals = (
                filtered_df["uncertainty_score"].values.astype(float)
                if "uncertainty_score" in filtered_df.columns
                else None
            )

            final_scores, subscores_list, active_strategy_used = self.scorer.score_candidates(
                performance_scores=perf_vals,
                uncertainty_scores=unc_vals,
                proximity_scores=proximity_scores,
                diversity_scores=diversity_vector,
                mutations_list=mutations_list,
                has_structure_mapping=has_structure_mapping,
                gate0_validated=gate0_validated,
            )

            # Mask out already selected indices
            for s_idx in selected_indices:
                final_scores[s_idx] = -float("inf")

            # Pick best candidate
            best_idx = int(np.argmax(final_scores))
            selected_indices.append(best_idx)
            available_indices.remove(best_idx)

            row_best = filtered_df.iloc[best_idx]
            sub_best = subscores_list[best_idx]
            prox_best = prox_results_map[best_idx]

            # Cost category proxy
            cost_val = compute_chemistry_cost_proxy(str(row_best.get("mutations", "WT")), has_structure_mapping[best_idx])
            cost_cat = "proxy-low" if cost_val <= 1.5 else ("proxy-medium" if cost_val <= 2.5 else "proxy-high")

            explanation = generate_candidate_explanation(
                rank=rank,
                subscores=sub_best,
                prox_res=prox_best,
                perf_raw=float(row_best["prediction"]),
                strategy=active_strategy_used,
            )

            unc_val = float(row_best["uncertainty_score"]) if "uncertainty_score" in row_best and pd.notna(row_best["uncertainty_score"]) else None

            candidate = SelectedCandidate(
                variant_id=str(row_best["variant_id"]),
                parent_enzyme=str(row_best.get("parent_enzyme", "IsPETase")),
                mutations=str(row_best.get("mutations", "WT")),
                predicted_performance=float(row_best["prediction"]),
                uncertainty=unc_val,
                proximity_score=prox_best.proximity_score,
                diversity_score=float(diversity_vector[best_idx]),
                estimated_chemistry_cost=cost_cat,
                acquisition_score=float(final_scores[best_idx]),
                selection_rank=rank,
                selection_reason=explanation,
                structure_mapping_status=prox_best.structure_mapping_status,
            )
            selected_candidates.append(candidate)

        summary_meta = {
            "requested_budget": budget,
            "selected_count": len(selected_candidates),
            "selection_shortfall": max(0, budget - len(selected_candidates)),
            "active_strategy": active_strategy_used,
            "gate0_validated": gate0_validated,
            "filter_metadata": filter_meta,
            "n_candidates_initial": n_input,
            "n_candidates_filtered": n_filtered,
        }

        return selected_candidates, summary_meta
