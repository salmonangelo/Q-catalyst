"""Multi-component composite uncertainty score combining ensemble, OOD, and conformal signals."""

from typing import Dict, Optional, Tuple
import numpy as np

from protein_ai.config import UncertaintyConfig


class CompositeUncertaintyScorer:
    """Combines normalized ensemble disagreement, OOD geometric distance, and conformal intervals."""

    def __init__(self, config: Optional[UncertaintyConfig] = None):
        self.config = config or UncertaintyConfig()
        self.w_ens = self.config.weight_ensemble
        self.w_ood = self.config.weight_ood
        self.w_conf = self.config.weight_conformal

    def compute_composite_score(
        self,
        ensemble_std: np.ndarray,
        ood_scores: np.ndarray,
        conformal_width: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Calculate composite uncertainty score U in [0, 1].

        Args:
            ensemble_std: Raw ensemble prediction standard deviations.
            ood_scores: Normalized OOD geometric distances.
            conformal_width: Optional conformal prediction interval widths.

        Returns:
            Tuple of (composite_uncertainty_array: np.ndarray, active_weights_dict: Dict).
        """
        # 1. Normalize ensemble std into [0, 1]
        std_arr = np.asarray(ensemble_std, dtype=float)
        std_max = np.max(std_arr) if len(std_arr) > 0 and np.max(std_arr) > 1e-6 else 1.0
        norm_std = np.clip(std_arr / std_max, 0.0, 1.0)

        # 2. OOD scores are already in [0, 1]
        norm_ood = np.clip(np.asarray(ood_scores, dtype=float), 0.0, 1.0)

        # 3. Normalize conformal width if available
        if conformal_width is not None:
            w_arr = np.asarray(conformal_width, dtype=float)
            w_max = np.max(w_arr) if len(w_arr) > 0 and np.max(w_arr) > 1e-6 else 1.0
            norm_conf = np.clip(w_arr / w_max, 0.0, 1.0)
            total_weight = self.w_ens + self.w_ood + self.w_conf
            w1 = self.w_ens / total_weight
            w2 = self.w_ood / total_weight
            w3 = self.w_conf / total_weight

            composite = (w1 * norm_std) + (w2 * norm_ood) + (w3 * norm_conf)
            weights_used = {"ensemble": w1, "ood": w2, "conformal": w3}
        else:
            total_weight = self.w_ens + self.w_ood
            w1 = self.w_ens / total_weight
            w2 = self.w_ood / total_weight

            composite = (w1 * norm_std) + (w2 * norm_ood)
            weights_used = {"ensemble": w1, "ood": w2, "conformal": 0.0}

        return composite.astype(np.float32), weights_used
