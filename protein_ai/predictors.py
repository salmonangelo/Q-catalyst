"""Lightweight supervised models for fitness and stability prediction on ESM features."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    xgb = None
    XGB_AVAILABLE = False

from protein_ai.config import PredictorConfig


class FitnessPredictor:
    """Configurable lightweight supervised predictor for PETase variant activity."""

    def __init__(self, config: Optional[PredictorConfig] = None):
        self.config = config or PredictorConfig()
        self.model: Optional[Any] = None
        self.target_name: str = self.config.target_column
        self.training_metadata: Dict[str, Any] = {}
        self._build_model()

    def _build_model(self) -> None:
        """Instantiate selected regressor."""
        m_type = self.config.model_type.lower()
        seed = self.config.random_seed

        if m_type == "ridge":
            self.model = Ridge(alpha=self.config.alpha, random_state=seed)
        elif m_type == "gradient_boosting":
            self.model = GradientBoostingRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=seed,
            )
        elif m_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=seed,
            )
        elif m_type == "xgboost" and XGB_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=seed,
                learning_rate=0.05,
            )
        else:
            # Default fallback to Ridge
            self.model = Ridge(alpha=self.config.alpha, random_state=seed)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[list] = None,
        split_strategy: str = "custom",
    ) -> None:
        """Fit model on training feature matrix and target vector."""
        if len(X_train) == 0 or len(y_train) == 0:
            raise ValueError("Cannot fit FitnessPredictor on empty training data.")

        # Ensure no NaNs in target
        mask = ~np.isnan(y_train)
        X_clean = X_train[mask]
        y_clean = y_train[mask]

        if len(y_clean) < 2:
            raise ValueError(f"Insufficient valid training samples ({len(y_clean)}) to fit predictor.")

        self.model.fit(X_clean, y_clean)

        self.training_metadata = {
            "model_type": self.config.model_type,
            "target_column": self.target_name,
            "n_train_samples": len(y_clean),
            "n_features": X_clean.shape[1],
            "split_strategy": split_strategy,
            "random_seed": self.config.random_seed,
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate point predictions."""
        if self.model is None:
            raise RuntimeError("Predictor has not been initialized.")
        return self.model.predict(X).astype(np.float32)

    def save(self, output_dir: Path | str, model_tag: str = "activity_predictor") -> Path:
        """Save model weights and metadata JSON."""
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        model_file = out_p / f"{model_tag}.joblib"
        meta_file = out_p / f"{model_tag}_metadata.json"

        joblib.dump(self.model, model_file)
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self.training_metadata, f, indent=2)

        return model_file

    def load(self, model_file: Path | str) -> None:
        """Load model from file."""
        p = Path(model_file)
        if not p.exists():
            raise FileNotFoundError(f"Model file not found: {p}")
        self.model = joblib.load(p)

        meta_p = p.parent / f"{p.stem}_metadata.json"
        if meta_p.exists():
            with open(meta_p, "r", encoding="utf-8") as f:
                self.training_metadata = json.load(f)
