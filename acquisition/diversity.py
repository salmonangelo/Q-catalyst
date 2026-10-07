"""Sequence diversity calculator and greedy redundancy penalization."""

from typing import Dict, List, Optional, Set
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from acquisition.config import DiversityConfig
from data.mutations import parse_mutations


class DiversityCalculator:
    """Measures sequence/representation diversity and penalizes candidate redundancy."""

    def __init__(self, config: Optional[DiversityConfig] = None):
        self.config = config or DiversityConfig()
        self.metric = self.config.metric

    def compute_similarity_matrix(
        self,
        embeddings: Optional[np.ndarray] = None,
        mutations_list: Optional[List[str]] = None,
    ) -> np.ndarray:
        """Calculate pairwise similarity matrix between candidate representations.

        Returns:
            N x N symmetric matrix with values in [0, 1].
        """
        if self.metric == "embedding_distance" and embeddings is not None:
            # Cosine similarity in embedding space
            norm_emb = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
            sim_matrix = np.dot(norm_emb, norm_emb.T)
            # Clip numerical float issues to [0, 1]
            return np.clip(sim_matrix, 0.0, 1.0).astype(np.float32)

        # Fallback to mutation token Jaccard similarity
        if mutations_list is None:
            raise ValueError("Must provide either embeddings or mutations_list to compute similarity matrix.")

        n = len(mutations_list)
        sim_matrix = np.eye(n, dtype=np.float32)

        # Parse mutation sets
        parsed_sets: List[Set[str]] = []
        for m_str in mutations_list:
            try:
                muts = parse_mutations(m_str)
                parsed_sets.append({m.to_string() for m in muts} if muts else {"WT"})
            except Exception:
                parsed_sets.append({"UNKNOWN"})

        for i in range(n):
            set_i = parsed_sets[i]
            for j in range(i + 1, n):
                set_j = parsed_sets[j]
                union_len = len(set_i.union(set_j))
                if union_len == 0:
                    sim = 1.0
                else:
                    sim = len(set_i.intersection(set_j)) / float(union_len)
                sim_matrix[i, j] = sim
                sim_matrix[j, i] = sim

        return sim_matrix

    def compute_candidate_diversity(
        self,
        candidate_idx: int,
        selected_indices: List[int],
        sim_matrix: np.ndarray,
    ) -> float:
        """Compute diversity score of candidate relative to currently selected candidates.

        Args:
            candidate_idx: Index of query candidate in similarity matrix.
            selected_indices: List of integer indices already selected.
            sim_matrix: Pairwise similarity matrix.

        Returns:
            Diversity score in [0, 1] (1.0 = completely novel, 0.0 = identical to an already selected candidate).
        """
        if not selected_indices:
            return 1.0

        # Maximum similarity to any already chosen candidate
        max_sim = float(np.max(sim_matrix[candidate_idx, selected_indices]))
        diversity = float(np.clip(1.0 - max_sim, 0.0, 1.0))
        return diversity

    def compute_batch_diversity(
        self,
        selected_indices: List[int],
        sim_matrix: np.ndarray,
    ) -> np.ndarray:
        """Compute diversity vector for all N candidates given selected subset."""
        n = sim_matrix.shape[0]
        if not selected_indices:
            return np.ones(n, dtype=np.float32)

        sub_sim = sim_matrix[:, selected_indices]  # (N, |S|)
        max_sim = np.max(sub_sim, axis=1)  # (N,)
        diversity = np.clip(1.0 - max_sim, 0.0, 1.0).astype(np.float32)
        return diversity
