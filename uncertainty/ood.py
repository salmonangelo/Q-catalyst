"""Out-Of-Distribution (OOD) distance estimator in sequence/embedding feature space."""

from typing import Optional
import numpy as np
from sklearn.neighbors import NearestNeighbors

from protein_ai.config import UncertaintyConfig


class OODDetector:
    """Computes geometric distance of query variants from the training distribution manifold."""

    def __init__(self, config: Optional[UncertaintyConfig] = None):
        self.config = config or UncertaintyConfig()
        self.k = self.config.ood_k_neighbors
        self.metric = self.config.ood_metric
        self.nn_model: Optional[NearestNeighbors] = None
        self.centroid: Optional[np.ndarray] = None
        self.train_distances_max: float = 1.0
        self.is_fitted: bool = False

    def fit(self, X_train: np.ndarray) -> None:
        """Fit OOD detector on training representations."""
        n_samples = len(X_train)
        if n_samples < 1:
            raise ValueError("Cannot fit OODDetector on empty training data.")

        effective_k = min(self.k, n_samples)
        self.nn_model = NearestNeighbors(n_neighbors=effective_k, metric="euclidean")
        self.nn_model.fit(X_train)

        self.centroid = np.mean(X_train, axis=0)

        # Compute internal training distance distribution for calibration
        distances, _ = self.nn_model.kneighbors(X_train)
        mean_k_dist = np.mean(distances, axis=1)
        self.train_distances_max = float(np.percentile(mean_k_dist, 95)) if len(mean_k_dist) > 0 else 1.0
        if self.train_distances_max <= 1e-6:
            self.train_distances_max = 1.0

        self.is_fitted = True

    def compute_ood_scores(self, X: np.ndarray) -> np.ndarray:
        """Compute normalized Out-of-Distribution distance scores in [0, 1].

        Args:
            X: Query feature matrix (N, D).

        Returns:
            1D array of OOD scores (higher values indicate greater distance from training data).
        """
        if not self.is_fitted or self.nn_model is None:
            raise RuntimeError("OODDetector must be fitted before computing scores.")

        distances, _ = self.nn_model.kneighbors(X)
        mean_dist = np.mean(distances, axis=1)

        # Normalize relative to 95th percentile of training internal distances
        normalized_scores = np.clip(mean_dist / self.train_distances_max, 0.0, 3.0) / 3.0
        return normalized_scores.astype(np.float32)
