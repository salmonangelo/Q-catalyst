# Q-Catalyst: Gate 0 Validation Report
## Uncertainty vs Prediction Error Empirical Assessment

**Dataset**: `variants`  
**Split Strategy**: `mutation_complexity`  
**Evaluation Samples (N)**: `1`  
**Uncertainty Method**: `composite (ens=0.40, ood=0.35, conf=0.25)`  
**Error Metric**: `MAE`  

---

### Key Empirical Findings

| Metric | Measured Value | Interpretation |
| :--- | :--- | :--- |
| **Spearman Rank Correlation** | `N/A` | Rank association between uncertainty and absolute error |
| **Spearman p-value** | `N/A` | Statistical significance |
| **Low-Uncertainty Mean Error** | `N/A` | Mean error for bottom 50% uncertainty candidates |
| **High-Uncertainty Mean Error** | `N/A` | Mean error for top 50% uncertainty candidates |
| **Error Ratio (High / Low)** | `N/A` | Ratio of error in high vs low uncertainty subsets |
| **Signal Strength Category** | **`INSUFFICIENT_DATA`** | Overall calibration assessment |
| **Gate 0 Decision** | **`FAILED / WEAK SIGNAL`** | Acquisition readiness |

---

### Methodological Recommendation
> **Acquire larger benchmark dataset before drawing conclusions on uncertainty quality.**

---

### Known Limitations & Caveats
- TEST RUN ONLY: Executed on synthetic fixture data for pipeline verification.
- Insufficient test samples (N=1) to compute statistically meaningful Gate-0 correlation.
