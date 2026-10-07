"""Utility functions for evaluation metrics, synthetic fixture generation, and device helpers."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, ndcg_score

from data.mutations import CANONICAL_AMINO_ACIDS, SingleMutation, apply_mutations_to_sequence
from data.schema import CANONICAL_COLUMNS, enforce_canonical_schema


def compute_regression_metrics(
    y_true: np.ndarray | List[float],
    y_pred: np.ndarray | List[float],
    k_list: Optional[List[int]] = None
) -> Dict[str, Optional[float]]:
    """Compute comprehensive regression and ranking metrics.

    Args:
        y_true: True numerical targets (e.g. experimental relative activity).
        y_pred: Predicted scores.
        k_list: List of K values for ranking metrics (default: [5, 10, 20]).

    Returns:
        Dictionary of computed metric values.
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    valid_mask = ~(np.isnan(yt) | np.isnan(yp))
    yt = yt[valid_mask]
    yp = yp[valid_mask]

    n_samples = len(yt)
    if n_samples < 2:
        return {
            "n_samples": n_samples,
            "spearman_rho": None,
            "spearman_pvalue": None,
            "pearson_r": None,
            "pearson_pvalue": None,
            "kendall_tau": None,
            "mae": None,
            "rmse": None,
        }

    # Spearman rank correlation
    if np.all(yt == yt[0]) or np.all(yp == yp[0]):
        spearman_corr, spearman_p = 0.0, 1.0
        pearson_corr, pearson_p = 0.0, 1.0
        kendall_corr = 0.0
    else:
        spearman_res = stats.spearmanr(yt, yp)
        spearman_corr = float(spearman_res.statistic)
        spearman_p = float(spearman_res.pvalue)

        pearson_res = stats.pearsonr(yt, yp)
        pearson_corr = float(pearson_res.statistic)
        pearson_p = float(pearson_res.pvalue)

        kendall_res = stats.kendalltau(yt, yp)
        kendall_corr = float(kendall_res.statistic)

    mae_val = float(mean_absolute_error(yt, yp))
    rmse_val = float(np.sqrt(mean_squared_error(yt, yp)))

    metrics: Dict[str, Optional[float]] = {
        "n_samples": n_samples,
        "spearman_rho": spearman_corr,
        "spearman_pvalue": spearman_p,
        "pearson_r": pearson_corr,
        "pearson_pvalue": pearson_p,
        "kendall_tau": kendall_corr,
        "mae": mae_val,
        "rmse": rmse_val,
    }

    # Top-K ranking metrics
    if k_list is None:
        k_list = [5, 10, 20]

    for k in k_list:
        if n_samples >= k:
            top_k_pred_idx = np.argsort(yp)[::-1][:k]
            top_k_true_idx = set(np.argsort(yt)[::-1][:k])
            precision_k = len(set(top_k_pred_idx).intersection(top_k_true_idx)) / float(k)
            metrics[f"precision_at_{k}"] = float(precision_k)

            # NDCG@K
            try:
                # Shift targets positive if needed for NDCG
                yt_pos = yt - np.min(yt) + 1e-5
                ndcg_k = float(ndcg_score([yt_pos], [yp], k=k))
                metrics[f"ndcg_at_{k}"] = ndcg_k
            except Exception:
                metrics[f"ndcg_at_{k}"] = None
        else:
            metrics[f"precision_at_{k}"] = None
            metrics[f"ndcg_at_{k}"] = None

    return metrics


def create_synthetic_variant_dataset(
    n_records: int = 24,
    random_seed: int = 42,
    parent_enzyme: str = "IsPETase",
    parent_sequence: str = (
        "QTNPYARGPNPTAASLEASAGPFTVRSFTVSRPSGYGAGTVYYPTNAGGTVGAIAIVPGYTARQSSIKWWGPR"
        "LASHGFVVITIDTNSTLDQPSSRSSQQMAALRQVASLNGTSSSPIYGKVDTARMGVMGWSMGGGGSLISAANN"
        "PSLRAAIPQAPWDSSTNFSSVTVPTLIFACENDSIAPVNSSALPIYDSMSRNAKQFLEINGGSHSCANSGNSN"
        "QALIGKKGVAWMKRFMDNDTRYSTFACENPNSTRVSDFRTANCS"
    ),
) -> pd.DataFrame:
    """Generate a clearly-labeled synthetic dataset fixture for testing pipelines offline.

    All rows are explicitly stamped with data_source = 'synthetic_test_fixture'
    and data_quality_flag = 'SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA'.

    Args:
        n_records: Number of synthetic variants to construct.
        random_seed: PRNG seed.
        parent_enzyme: Name of parent scaffold.
        parent_sequence: Reference amino acid sequence.

    Returns:
        DataFrame conforming to canonical schema.
    """
    rng = np.random.RandomState(random_seed)
    seq_len = len(parent_sequence)
    aa_list = sorted(list(CANONICAL_AMINO_ACIDS))

    records = []
    # Row 0 is wild-type
    records.append({
        "variant_id": f"{parent_enzyme}_WT",
        "parent_enzyme": parent_enzyme,
        "sequence": parent_sequence,
        "mutations": "WT",
        "activity_value": 1.0,
        "activity_unit": "relative",
        "activity_rel_to_parent": 1.0,
        "Tm_C": 50.5,
        "dTm_vs_parent": 0.0,
        "temperature_C": 30.0,
        "pH": 7.0,
        "substrate": "PET film",
        "PET_crystallinity_pct": 10.0,
        "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA",
        "study_id": "SYNTHETIC_STUDY_1",
        "data_source": "synthetic_test_fixture",
    })

    for i in range(1, n_records):
        study_id = f"SYNTHETIC_STUDY_{(i % 4) + 1}"
        is_multi = (i % 3 == 0)

        if is_multi:
            # 2 point mutations
            pos1 = rng.randint(1, seq_len // 2)
            pos2 = rng.randint(seq_len // 2 + 1, seq_len + 1)
            orig1 = parent_sequence[pos1 - 1]
            orig2 = parent_sequence[pos2 - 1]
            target1 = rng.choice([a for a in aa_list if a != orig1])
            target2 = rng.choice([a for a in aa_list if a != orig2])
            muts = f"{orig1}{pos1}{target1};{orig2}{pos2}{target2}"
        else:
            pos = rng.randint(1, seq_len + 1)
            orig = parent_sequence[pos - 1]
            target = rng.choice([a for a in aa_list if a != orig])
            muts = f"{orig}{pos}{target}"

        seq = apply_mutations_to_sequence(parent_sequence, muts, offset=1)
        # Synthetic activity with non-linear functional landscape
        noise = rng.normal(0, 0.1)
        simulated_act = float(np.clip(1.0 + (rng.normal(0, 0.4) if not is_multi else rng.normal(-0.2, 0.6)) + noise, 0.05, 3.5))
        simulated_tm = float(50.5 + rng.normal(0, 2.5))

        records.append({
            "variant_id": f"{parent_enzyme}_var_{i:03d}",
            "parent_enzyme": parent_enzyme,
            "sequence": seq,
            "mutations": muts,
            "activity_value": simulated_act,
            "activity_unit": "relative",
            "activity_rel_to_parent": simulated_act,
            "Tm_C": simulated_tm,
            "dTm_vs_parent": float(simulated_tm - 50.5),
            "temperature_C": 30.0,
            "pH": 7.0,
            "substrate": "PET film",
            "PET_crystallinity_pct": 10.0,
            "data_quality_flag": "SYNTHETIC_FIXTURE_NOT_BENCHMARK_DATA",
            "study_id": study_id,
            "data_source": "synthetic_test_fixture",
        })

    df = pd.DataFrame(records)
    canonical = enforce_canonical_schema(df)
    canonical["data_source"] = "synthetic_test_fixture"
    return canonical
