"""Embedding extraction pipeline with disk caching and batch processing."""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from protein_ai.config import ESMConfig
from protein_ai.esm import ESMModelWrapper, get_esm_model


class EmbeddingExtractor:
    """Manages extraction and persistent disk-caching of protein sequence embeddings."""

    def __init__(
        self,
        config: Optional[ESMConfig] = None,
        model_wrapper: Optional[ESMModelWrapper] = None
    ):
        self.config = config or ESMConfig()
        self.model = model_wrapper or get_esm_model(self.config)
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, np.ndarray] = {}
        self._load_disk_cache()

    def _get_cache_file_path(self) -> Path:
        clean_model_name = self.model.model_name.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"embeddings_{clean_model_name}.npz"

    def _load_disk_cache(self) -> None:
        """Load persistent embedding cache if it exists."""
        cache_path = self._get_cache_file_path()
        if cache_path.exists():
            try:
                data = np.load(cache_path)
                for key in data.files:
                    self._memory_cache[key] = data[key]
            except Exception as e:
                print(f"Warning: Failed to load disk embedding cache ({e}). Starting fresh.")

    def _save_disk_cache(self) -> None:
        """Save memory cache to disk."""
        if not self._memory_cache:
            return
        cache_path = self._get_cache_file_path()
        try:
            np.savez_compressed(cache_path, **self._memory_cache)
        except Exception as e:
            print(f"Warning: Failed to save disk embedding cache: {e}")

    @staticmethod
    def _hash_sequence(sequence: str) -> str:
        return hashlib.sha256(sequence.strip().upper().encode("utf-8")).hexdigest()[:16]

    def embed_sequence(self, sequence: str) -> np.ndarray:
        """Get embedding for single sequence (using memory/disk cache where available)."""
        seq = sequence.strip().upper()
        h = self._hash_sequence(seq)
        if h in self._memory_cache:
            return self._memory_cache[h]

        emb = self.model.extract_sequence_embedding(seq)
        self._memory_cache[h] = emb
        return emb

    def embed_dataframe(
        self,
        df: pd.DataFrame,
        sequence_column: str = "sequence",
        variant_id_column: str = "variant_id",
    ) -> Tuple[np.ndarray, List[str]]:
        """Extract embeddings for all sequences in a DataFrame with batching and cache logging.

        Args:
            df: Input DataFrame.
            sequence_column: Column name for amino acid sequences.
            variant_id_column: Column name for variant IDs.

        Returns:
            Tuple of (embeddings_matrix: np.ndarray of shape (N, D), list_of_variant_ids).
        """
        if sequence_column not in df.columns:
            raise KeyError(f"Sequence column '{sequence_column}' not found in DataFrame.")

        variant_ids = (
            df[variant_id_column].tolist()
            if variant_id_column in df.columns
            else [f"row_{i}" for i in range(len(df))]
        )

        embeddings = []
        cache_hits = 0
        cache_misses = 0

        for seq in df[sequence_column]:
            if pd.isna(seq) or not str(seq).strip():
                raise ValueError("Encountered empty or null sequence during embedding extraction.")

            seq_str = str(seq).strip().upper()
            h = self._hash_sequence(seq_str)

            if h in self._memory_cache:
                embeddings.append(self._memory_cache[h])
                cache_hits += 1
            else:
                emb = self.model.extract_sequence_embedding(seq_str)
                self._memory_cache[h] = emb
                embeddings.append(emb)
                cache_misses += 1

        if cache_misses > 0 and self.config.use_cache:
            self._save_disk_cache()

        matrix = np.vstack(embeddings).astype(np.float32)
        return matrix, variant_ids
