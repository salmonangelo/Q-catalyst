"""Split Conformal Prediction for distribution-free finite-sample prediction intervals."""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

from protein_ai.config import UncertaintyConfig


@dataclass(frozen=True)
class ConformalInterval:
    """Conformal prediction interval output."""
    lower_bound: np.ndarray
    upper_bound: np.ndarray
    interval_width: np.ndarray
    quantile_q: float
    target_coverage: float
    n_calibration_samples: int


class ConformalCalibrator:
    """Implements standard Split Conformal Prediction with exact finite-sample validity."""

    def __init__(self, config: Optional[UncertaintyConfig] = None):
        self.config = config or UncertaintyConfig()
        self.alpha = self.config.conformal_alpha
        self.quantile_q: Optional[float] = None
        self.n_calib: int = 0
        self.is_calibrated: bool = False

    def calibrate(self, y_calib_true: np.ndarray, y_calib_pred: np.ndarray) -> float:
        """Compute conformal non-conformity quantile on held-out calibration set.

        Args:
            y_calib_true: Ground truth target values on calibration fold.
            y_calib_pred: Model predictions on calibration fold.

        Returns:
            Computed non-conformity score quantile q.
        """
        y_true = np.asarray(y_calib_true, dtype=float)
        y_pred = np.asarray(y_calib_pred, dtype=float)

        # Filter NaNs
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_t = y_true[mask]
        y_p = y_pred[mask]

        n = len(y_t)
        if n < 1:
            raise ValueError("Calibration set must contain at least 1 valid observation.")

        # Absolute residual non-conformity scores
        residuals = np.abs(y_t - y_p)

        # Standard split conformal finite-sample adjusted quantile level
        q_level = min(1.0, np.ceil((n + 1) * (1.0 - self.alpha)) / float(n))
        self.quantile_q = float(np.quantile(residuals, q_level, method="higher"))
        self.n_calib = n
        self.is_calibrated = True

        return self.quantile_q

    def predict_intervals(self, y_pred: np.ndarray) -> ConformalInterval:
        """Construct conformal prediction intervals around point predictions.

        Args:
            y_pred: Point predictions for query instances.

        Returns:
            ConformalInterval dataclass.
        """
        if not self.is_calibrated or self.quantile_q is None:
            raise RuntimeError("ConformalCalibrator must be calibrated on validation data before generating intervals.")

        yp = np.asarray(y_pred, dtype=float)
        lower = (yp - self.quantile_q).astype(np.float32)
        upper = (yp + self.quantile_q).astype(np.float32)
        width = np.full_like(yp, fill_value=2.0 * self.quantile_q, dtype=np.float32)

        return ConformalInterval(
            lower_bound=lower,
            upper_bound=upper,
            interval_width=width,
            quantile_q=self.quantile_q,
            target_coverage=float(1.0 - self.alpha),
            n_calibration_samples=self.n_calib,
        )
