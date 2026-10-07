"""Feature pipeline combining ESM representations, zero-shot mutation scores, and normalization."""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from protein_ai.embeddings import EmbeddingExtractor
from protein_ai.mutation_scoring import MutationScorer


class FeaturePipeline:
    """Extracts, concatenates, and standardizes multi-modal protein sequence features."""

    def __init__(
        self,
        embedding_extractor: Optional[EmbeddingExtractor] = None,
        mutation_scorer: Optional[MutationScorer] = None,
        normalize_features: bool = True,
    ):
        self.embedding_extractor = embedding_extractor or EmbeddingExtractor()
        self.mutation_scorer = mutation_scorer or MutationScorer()
        self.normalize_features = normalize_features
        self.scaler: Optional[StandardScaler] = None
        self.is_fitted: bool = False
        self.feature_names: List[str] = []

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Extract features and fit standard scaler strictly on training DataFrame.

        Args:
            df: Training DataFrame.

        Returns:
            Tuple of (feature_matrix, list_of_variant_ids).
        """
        raw_features, variant_ids = self._extract_raw_features(df)

        if self.normalize_features:
            self.scaler = StandardScaler()
            features = self.scaler.fit_transform(raw_features)
        else:
            features = raw_features

        self.is_fitted = True
        return features.astype(np.float32), variant_ids

    def transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Transform validation/test DataFrame using fitted parameters.

        Args:
            df: Evaluation DataFrame.

        Returns:
            Tuple of (feature_matrix, list_of_variant_ids).
        """
        if not self.is_fitted and self.normalize_features:
            raise RuntimeError("FeaturePipeline must be fitted on training data before calling transform().")

        raw_features, variant_ids = self._extract_raw_features(df)

        if self.normalize_features and self.scaler is not None:
            features = self.scaler.transform(raw_features)
        else:
            features = raw_features

        return features.astype(np.float32), variant_ids

    def _extract_raw_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Extract embeddings and mutation score features."""
        # 1. Sequence embeddings (N, D)
        embeddings, variant_ids = self.embedding_extractor.embed_dataframe(df)

        # 2. Mutation scores (N, 1)
        score_df = self.mutation_scorer.score_dataframe(df)
        mut_scores = score_df["mutation_score"].values.reshape(-1, 1).astype(np.float32)

        # 3. Concatenate
        combined = np.hstack([embeddings, mut_scores])

        # Track feature names
        emb_dim = embeddings.shape[1]
        self.feature_names = [f"esm_dim_{i}" for i in range(emb_dim)] + ["mutation_score"]

        return combined, variant_ids
