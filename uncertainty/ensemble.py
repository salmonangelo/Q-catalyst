"""Ensemble disagreement estimator for epistemic model uncertainty."""

from typing import List, Optional, Tuple
import numpy as np
from sklearn.linear_model import Ridge

from protein_ai.config import PredictorConfig, UncertaintyConfig
from protein_ai.predictors import FitnessPredictor


class EnsembleEstimator:
    """Trains an ensemble of bootstrap/subsampled models to quantify prediction disagreement."""

    def __init__(
        self,
        predictor_config: Optional[PredictorConfig] = None,
        uncertainty_config: Optional[UncertaintyConfig] = None,
    ):
        self.p_cfg = predictor_config or PredictorConfig()
        self.u_cfg = uncertainty_config or UncertaintyConfig()
        self.models: List[FitnessPredictor] = []
        self.is_fitted: bool = False

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Fit M ensemble members on random bootstrap subsamples of the training set.

        Args:
            X_train: Training feature matrix (N, D).
            y_train: Training targets (N,).
        """
        n_samples = len(X_train)
        if n_samples < 2:
            raise ValueError(f"Need at least 2 training samples to fit ensemble, got {n_samples}")

        self.models.clear()
        rng = np.random.RandomState(self.p_cfg.random_seed)

        n_subsample = max(2, int(np.round(self.u_cfg.ensemble_subsample_ratio * n_samples)))

        for i in range(self.u_cfg.ensemble_size):
            # Bootstrap sample indices with replacement
            sample_idx = rng.choice(n_samples, size=n_subsample, replace=True)
            X_sub = X_train[sample_idx]
            y_sub = y_train[sample_idx]

            cfg_i = self.p_cfg.model_copy()
            cfg_i.random_seed = self.p_cfg.random_seed + (i * 17) + 1

            member = FitnessPredictor(config=cfg_i)
            member.fit(X_sub, y_sub, split_strategy="ensemble_bootstrap")
            self.models.append(member)

        self.is_fitted = True

    def predict_with_disagreement(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute ensemble mean prediction and standard deviation (disagreement).

        Args:
            X: Query feature matrix (N, D).

        Returns:
            Tuple of (ensemble_mean: np.ndarray, ensemble_std: np.ndarray).
        """
        if not self.is_fitted or not self.models:
            raise RuntimeError("EnsembleEstimator must be fitted before predicting.")

        preds_matrix = np.vstack([m.predict(X) for m in self.models])  # Shape: (M, N)

        ensemble_mean = np.mean(preds_matrix, axis=0).astype(np.float32)
        ensemble_std = np.std(preds_matrix, axis=0, ddof=1).astype(np.float32)

        return ensemble_mean, ensemble_std
