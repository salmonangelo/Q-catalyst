"""Gate 0 Validation: Empirical evaluation of whether uncertainty predicts model error."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats


@dataclass
class Gate0Report:
    """Structured results of the Gate-0 uncertainty calibration experiment."""
    dataset_name: str
    split_strategy: str
    n_samples: int
    uncertainty_method: str
    error_metric: str
    spearman_correlation: Optional[float]
    spearman_pvalue: Optional[float]
    pearson_correlation: Optional[float]
    low_uncertainty_mean_error: Optional[float]
    high_uncertainty_mean_error: Optional[float]
    error_ratio_high_vs_low: Optional[float]
    useful_signal: bool
    signal_strength: str  # 'STRONG', 'MODERATE', 'WEAK', 'NO_SIGNAL'
    recommendation: str
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save_json(self, output_path: Path | str) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def save_markdown(self, output_path: Path | str) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        md = f"""# Q-Catalyst: Gate 0 Validation Report
## Uncertainty vs Prediction Error Empirical Assessment

**Dataset**: `{self.dataset_name}`  
**Split Strategy**: `{self.split_strategy}`  
**Evaluation Samples (N)**: `{self.n_samples}`  
**Uncertainty Method**: `{self.uncertainty_method}`  
**Error Metric**: `{self.error_metric}`  

---

### Key Empirical Findings

| Metric | Measured Value | Interpretation |
| :--- | :--- | :--- |
| **Spearman Rank Correlation** | `{self.spearman_correlation if self.spearman_correlation is not None else 'N/A'}` | Rank association between uncertainty and absolute error |
| **Spearman p-value** | `{f'{self.spearman_pvalue:.4e}' if self.spearman_pvalue is not None else 'N/A'}` | Statistical significance |
| **Low-Uncertainty Mean Error** | `{f'{self.low_uncertainty_mean_error:.4f}' if self.low_uncertainty_mean_error is not None else 'N/A'}` | Mean error for bottom 50% uncertainty candidates |
| **High-Uncertainty Mean Error** | `{f'{self.high_uncertainty_mean_error:.4f}' if self.high_uncertainty_mean_error is not None else 'N/A'}` | Mean error for top 50% uncertainty candidates |
| **Error Ratio (High / Low)** | `{f'{self.error_ratio_high_vs_low:.2f}x' if self.error_ratio_high_vs_low is not None else 'N/A'}` | Ratio of error in high vs low uncertainty subsets |
| **Signal Strength Category** | **`{self.signal_strength}`** | Overall calibration assessment |
| **Gate 0 Decision** | **`{'PASSED (Useful Signal Detected)' if self.useful_signal else 'FAILED / WEAK SIGNAL'}`** | Acquisition readiness |

---

### Methodological Recommendation
> **{self.recommendation}**

---

### Known Limitations & Caveats
"""
        for lim in self.limitations:
            md += f"- {lim}\n"

        with open(p, "w", encoding="utf-8") as f:
            f.write(md)


def evaluate_gate0(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    uncertainty_scores: np.ndarray,
    dataset_name: str = "curated_variants",
    split_strategy: str = "mutation_complexity",
    uncertainty_method: str = "composite (ensemble + OOD + conformal)",
    is_synthetic_fixture: bool = False,
) -> Gate0Report:
    """Execute Gate 0 uncertainty validation experiment on held-out test data.

    Args:
        y_true: Ground truth target values on test set.
        y_pred: Predicted target values.
        uncertainty_scores: Estimated uncertainty scores U.
        dataset_name: Name of evaluated dataset.
        split_strategy: Partition strategy name.
        uncertainty_method: Description of uncertainty aggregation.
        is_synthetic_fixture: Flag indicating test fixture data.

    Returns:
        Gate0Report object.
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)
    u = np.asarray(uncertainty_scores, dtype=float)

    mask = ~(np.isnan(yt) | np.isnan(yp) | np.isnan(u))
    yt = yt[mask]
    yp = yp[mask]
    u = u[mask]

    n = len(yt)
    limitations = []
    if is_synthetic_fixture:
        limitations.append("TEST RUN ONLY: Executed on synthetic fixture data for pipeline verification.")

    if n < 4:
        limitations.append(f"Insufficient test samples (N={n}) to compute statistically meaningful Gate-0 correlation.")
        return Gate0Report(
            dataset_name=dataset_name,
            split_strategy=split_strategy,
            n_samples=n,
            uncertainty_method=uncertainty_method,
            error_metric="MAE",
            spearman_correlation=None,
            spearman_pvalue=None,
            pearson_correlation=None,
            low_uncertainty_mean_error=None,
            high_uncertainty_mean_error=None,
            error_ratio_high_vs_low=None,
            useful_signal=False,
            signal_strength="INSUFFICIENT_DATA",
            recommendation="Acquire larger benchmark dataset before drawing conclusions on uncertainty quality.",
            limitations=limitations,
        )

    # 1. Absolute prediction error
    abs_errors = np.abs(yt - yp)

    # 2. Correlation between uncertainty and error
    if np.all(abs_errors == abs_errors[0]) or np.all(u == u[0]):
        spearman_rho, spearman_p = 0.0, 1.0
        pearson_r = 0.0
    else:
        s_res = stats.spearmanr(u, abs_errors)
        spearman_rho = float(s_res.statistic)
        spearman_p = float(s_res.pvalue)

        p_res = stats.pearsonr(u, abs_errors)
        pearson_r = float(p_res.statistic)

    # 3. Stratified error comparison (median split)
    median_u = np.median(u)
    low_u_mask = u <= median_u
    high_u_mask = u > median_u

    low_err = float(np.mean(abs_errors[low_u_mask])) if np.any(low_u_mask) else 0.0
    high_err = float(np.mean(abs_errors[high_u_mask])) if np.any(high_u_mask) else 0.0

    ratio = float(high_err / (low_err + 1e-6)) if low_err > 0 else 1.0

    # 4. Signal strength categorization
    if spearman_rho >= 0.35 and ratio > 1.25:
        strength = "STRONG"
        useful = True
        rec = "Uncertainty reliably flags high-error predictions. Safe to proceed to active learning acquisition."
    elif spearman_rho >= 0.15 and ratio >= 1.05:
        strength = "MODERATE"
        useful = True
        rec = "Moderate error tracking signal detected. Recommend using uncertainty with conservative acquisition weights."
    elif spearman_rho >= 0.05:
        strength = "WEAK"
        useful = False
        rec = "Weak correlation with error. Acquisition policy should use hybrid exploration/exploitation fallback."
    else:
        strength = "NO_SIGNAL"
        useful = False
        rec = "Uncertainty does not track error on this split. Fall back to pure ensemble variance or greedy acquisition."

    return Gate0Report(
        dataset_name=dataset_name,
        split_strategy=split_strategy,
        n_samples=n,
        uncertainty_method=uncertainty_method,
        error_metric="MAE",
        spearman_correlation=spearman_rho,
        spearman_pvalue=spearman_p,
        pearson_correlation=pearson_r,
        low_uncertainty_mean_error=low_err,
        high_uncertainty_mean_error=high_err,
        error_ratio_high_vs_low=ratio,
        useful_signal=useful,
        signal_strength=strength,
        recommendation=rec,
        limitations=limitations,
    )
