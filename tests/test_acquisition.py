"""Unit tests for Smart Acquisition Gate: proximity, filtering, diversity, scoring, and selector."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from acquisition.config import AcquisitionConfig, AcquisitionWeights, ProximityConfig
from acquisition.diversity import DiversityCalculator
from acquisition.filters import PerformanceFilter
from acquisition.proximity import ActiveSiteProximityCalculator
from acquisition.scoring import AcquisitionScorer, compute_chemistry_cost_proxy
from acquisition.selector import SelectedCandidate, SmartAcquisitionSelector, generate_candidate_explanation


@pytest.fixture
def mock_candidates_df():
    # 20 candidate variants with simulated predictions and uncertainties
    records = []
    mut_pool = [
        "WT",
        "S160A",
        "D206G",
        "H237A",
        "Y87A",
        "M161A",
        "W185A",
        "W159A",
        "S160A;D206G",
        "Q35A",
        "N233A",
        "T240A",
        "S100A",
        "G200A",
        "L150A",
        "V120A",
        "P50A",
        "R90A",
        "F100A",
        "K130A",
    ]
    for i, m in enumerate(mut_pool):
        records.append({
            "variant_id": f"var_{i:02d}_{m.replace(';', '_')}",
            "parent_enzyme": "IsPETase",
            "mutations": m,
            "prediction": 1.0 + (0.1 * i) if i % 2 == 0 else 0.8 + (0.05 * i),
            "uncertainty_score": 0.2 + (0.03 * i),
            "ensemble_std": 0.05 + (0.01 * i),
            "ood_score": 0.1 + (0.02 * i),
        })
    return pd.DataFrame(records)


def test_active_site_proximity_calculator():
    calc = ActiveSiteProximityCalculator()

    # 1. Wild-type -> mapped_wt, distance = 0, score = 1.0
    res_wt = calc.calculate_proximity("v_wt", "WT", parent_enzyme="IsPETase")
    assert res_wt.structure_mapping_status == "mapped_wt"
    assert res_wt.min_distance_angstrom == 0.0
    assert res_wt.proximity_score == 1.0

    # 2. Catalytic residue Ser160 -> mapped, distance = 0 to pos 160
    res_s160 = calc.calculate_proximity("v_s160", "S160A", parent_enzyme="IsPETase")
    assert res_s160.structure_mapping_status == "mapped"
    assert res_s160.closest_active_site_residue == 160
    assert res_s160.min_distance_angstrom == 0.0
    assert res_s160.proximity_score == 1.0

    # 3. Far residue (e.g. Q35 at N-terminus) -> higher distance, lower proximity score
    res_q35 = calc.calculate_proximity("v_q35", "Q35A", parent_enzyme="IsPETase")
    if res_q35.structure_mapping_status == "mapped":
        assert res_q35.min_distance_angstrom > 10.0
        assert res_q35.proximity_score < 0.50

    # 4. Out-of-bounds residue -> missing_residue status
    res_out = calc.calculate_proximity("v_out", "S500A", parent_enzyme="IsPETase")
    assert res_out.structure_mapping_status in ("missing_residue", "outside_structure")
    assert res_out.proximity_score is None

    # 5. Non-IsPETase parent -> unmapped_parent status
    res_lcc = calc.calculate_proximity("v_lcc", "S160A", parent_enzyme="LCC")
    assert res_lcc.structure_mapping_status == "unmapped_parent"
    assert res_lcc.proximity_score is None


def test_performance_filter(mock_candidates_df):
    # Quantile filter: Keep top 50%
    cfg_q = AcquisitionConfig(performance_quantile=0.50, performance_threshold=None)
    filter_q = PerformanceFilter(cfg_q)
    filtered_q, meta_q = filter_q.filter_candidates(mock_candidates_df)
    assert len(filtered_q) <= len(mock_candidates_df)
    assert len(filtered_q) == 10
    assert meta_q["n_passed"] == 10

    # Absolute threshold filter: Keep prediction >= 1.50
    cfg_t = AcquisitionConfig(performance_quantile=None, performance_threshold=1.50)
    filter_t = PerformanceFilter(cfg_t)
    filtered_t, meta_t = filter_t.filter_candidates(mock_candidates_df)
    assert (filtered_t["prediction"] >= 1.50).all()


def test_diversity_calculator():
    div_calc = DiversityCalculator()
    muts = ["S160A", "S160A", "D206G", "W185A;W159A"]

    sim_matrix = div_calc.compute_similarity_matrix(mutations_list=muts)
    assert sim_matrix.shape == (4, 4)
    # Identical mutations have similarity 1.0
    assert sim_matrix[0, 1] == 1.0
    # Different mutations have lower similarity
    assert sim_matrix[0, 2] < 1.0

    # Test candidate diversity relative to already selected candidate 0
    d_same = div_calc.compute_candidate_diversity(1, [0], sim_matrix)
    d_diff = div_calc.compute_candidate_diversity(2, [0], sim_matrix)

    assert d_same == 0.0  # Zero diversity relative to identical candidate
    assert d_diff > 0.50  # High diversity relative to distinct candidate


def test_chemistry_cost_proxy():
    cost_wt = compute_chemistry_cost_proxy("WT", has_structure_mapping=True)
    cost_single = compute_chemistry_cost_proxy("S160A", has_structure_mapping=True)
    cost_multi = compute_chemistry_cost_proxy("S160A;D206G;H237A", has_structure_mapping=True)
    cost_unmapped = compute_chemistry_cost_proxy("S160A", has_structure_mapping=False)

    assert cost_wt == 1.0
    assert cost_single == 1.5
    assert cost_multi == 2.5
    assert cost_unmapped == 2.5  # +1.0 overhead for missing structure mapping


def test_acquisition_scoring_strategies(mock_candidates_df):
    scorer = AcquisitionScorer()
    perf = mock_candidates_df["prediction"].values
    unc = mock_candidates_df["uncertainty_score"].values
    div = np.ones(len(perf))
    prox = np.ones(len(perf)) * 0.8
    muts = mock_candidates_df["mutations"].tolist()

    # 1. Performance only
    scores_p, _, strat_p = scorer.score_candidates(
        performance_scores=perf,
        uncertainty_scores=unc,
        proximity_scores=prox,
        diversity_scores=div,
        mutations_list=muts,
        strategy_override="performance_only",
    )
    assert strat_p == "performance_only"
    # Highest prediction must have score 1.0
    assert np.argmax(scores_p) == np.argmax(perf)

    # 2. Uncertainty only
    scores_u, _, strat_u = scorer.score_candidates(
        performance_scores=perf,
        uncertainty_scores=unc,
        proximity_scores=prox,
        diversity_scores=div,
        mutations_list=muts,
        strategy_override="uncertainty_only",
    )
    assert strat_u == "uncertainty_only"
    assert np.argmax(scores_u) == np.argmax(unc)

    # 3. Mechanism aware without uncertainty fallback
    scores_fb, _, strat_fb = scorer.score_candidates(
        performance_scores=perf,
        uncertainty_scores=unc,
        proximity_scores=prox,
        diversity_scores=div,
        mutations_list=muts,
        strategy_override="mechanism_aware",
        gate0_validated=False,  # Triggers fallback
    )
    assert strat_fb == "mechanism_aware_without_uncertainty"


def test_smart_acquisition_selector_budget_and_explanations(mock_candidates_df):
    cfg = AcquisitionConfig(chemistry_budget=5, performance_quantile=0.50)
    selector = SmartAcquisitionSelector(config=cfg)

    selected, meta = selector.select_candidates(mock_candidates_df, gate0_validated=True)

    # Obey budget
    assert len(selected) == 5
    assert meta["selected_count"] == 5
    assert meta["selection_shortfall"] == 0

    # Ranks must be 1 to 5
    ranks = [c.selection_rank for c in selected]
    assert ranks == [1, 2, 3, 4, 5]

    # Check that explanation is generated
    for c in selected:
        assert isinstance(c.selection_reason, str)
        assert len(c.selection_reason) > 10
        assert str(c.selection_rank) in c.selection_reason
