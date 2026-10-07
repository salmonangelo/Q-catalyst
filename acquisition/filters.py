"""Candidate filtering based on predicted performance thresholds and quantiles."""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd

from acquisition.config import AcquisitionConfig


class PerformanceFilter:
    """Filters candidate variant pools based on predicted performance thresholds or quantiles."""

    def __init__(self, config: Optional[AcquisitionConfig] = None):
        self.config = config or AcquisitionConfig()

    def filter_candidates(
        self,
        df: pd.DataFrame,
        score_column: str = "prediction"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Apply performance filtering to candidate DataFrame.

        Args:
            df: Input DataFrame containing predicted performance scores.
            score_column: Target prediction column to filter on.

        Returns:
            Tuple of (filtered_dataframe, filter_metadata_dict).
        """
        if score_column not in df.columns:
            raise KeyError(f"Score column '{score_column}' not found in candidate DataFrame.")

        n_initial = len(df)
        if n_initial == 0:
            return df.copy(), {"n_initial": 0, "n_passed": 0, "cutoff_value": None}

        # Drop NaN predictions
        valid_df = df[df[score_column].notna()].copy()
        if valid_df.empty:
            return valid_df, {"n_initial": n_initial, "n_passed": 0, "cutoff_value": None}

        scores = valid_df[score_column].values.astype(float)
        cutoff: Optional[float] = None
        filter_type = "none"

        # 1. Check explicit threshold
        if self.config.performance_threshold is not None:
            cutoff = float(self.config.performance_threshold)
            filtered_df = valid_df[valid_df[score_column] >= cutoff].copy()
            filter_type = "absolute_threshold"

        # 2. Check quantile
        elif self.config.performance_quantile is not None:
            q = float(np.clip(self.config.performance_quantile, 0.0, 1.0))
            cutoff = float(np.quantile(scores, q))
            filtered_df = valid_df[valid_df[score_column] >= cutoff].copy()
            filter_type = f"quantile_{q:.2f}"

        else:
            filtered_df = valid_df.copy()
            filter_type = "pass_all"

        metadata = {
            "n_initial": n_initial,
            "n_valid_predictions": len(valid_df),
            "n_passed": len(filtered_df),
            "filter_type": filter_type,
            "cutoff_value": cutoff,
            "min_score": float(np.min(scores)) if len(scores) > 0 else None,
            "max_score": float(np.max(scores)) if len(scores) > 0 else None,
            "median_score": float(np.median(scores)) if len(scores) > 0 else None,
        }

        return filtered_df, metadata
