"""Data splitting strategies for PETase variant datasets to prevent data leakage."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GroupShuffleSplit, KFold, ShuffleSplit

from configs.config_schema import QCatalystConfig, load_config
from data.mutations import parse_mutations


@dataclass
class SplitManifest:
    """Represents a concrete train/val/test data partition."""
    strategy: str
    random_seed: int
    train_count: int
    val_count: int
    test_count: int
    train_variant_ids: List[str]
    val_variant_ids: List[str]
    test_variant_ids: List[str]
    leakage_assessment: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save_json(self, output_path: Path | str) -> None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class DatasetSplitter:
    """Executes configurable, leakage-aware dataset splitting."""

    def __init__(self, config: Optional[QCatalystConfig] = None):
        self.config = config or load_config()

    def split(
        self,
        df: pd.DataFrame,
        strategy: Optional[str] = None,
        random_seed: Optional[int] = None,
        train_ratio: Optional[float] = None,
        val_ratio: Optional[float] = None,
        test_ratio: Optional[float] = None,
    ) -> SplitManifest:
        """Partition DataFrame into train, validation, and test subsets.

        Strategies:
            - 'study_grouped': Group by study_id to evaluate generalization to unseen labs/assays.
            - 'parent_grouped': Group by parent_enzyme to evaluate homolog transfer.
            - 'mutation_complexity': Train on single-site mutants, evaluate on multi-site mutants.
            - 'random': Standard random split (with explicit data leakage warning).

        Args:
            df: Curated variants DataFrame.
            strategy: Split strategy name.
            random_seed: PRNG seed for reproducibility.
            train_ratio: Fraction of data in training split.
            val_ratio: Fraction of data in validation split.
            test_ratio: Fraction of data in test split.

        Returns:
            SplitManifest with variant IDs and leakage assessment.
        """
        strat = strategy or self.config.splitting.default_strategy
        seed = random_seed if random_seed is not None else self.config.splitting.random_seed
        tr_r = train_ratio if train_ratio is not None else self.config.splitting.train_ratio
        val_r = val_ratio if val_ratio is not None else self.config.splitting.val_ratio
        te_r = test_ratio if test_ratio is not None else self.config.splitting.test_ratio

        if not np.isclose(tr_r + val_r + te_r, 1.0):
            raise ValueError(f"Split ratios must sum to 1.0, got {tr_r + val_r + te_r:.4f}")

        if "variant_id" not in df.columns:
            raise KeyError("DataFrame must contain 'variant_id' column for splitting.")

        if strat == "study_grouped":
            return self._split_study_grouped(df, seed, tr_r, val_r, te_r)
        elif strat == "parent_grouped":
            return self._split_parent_grouped(df, seed, tr_r, val_r, te_r)
        elif strat == "mutation_complexity":
            return self._split_mutation_complexity(df, seed, val_r, te_r)
        elif strat == "random":
            return self._split_random(df, seed, tr_r, val_r, te_r)
        else:
            raise ValueError(
                f"Unknown split strategy '{strat}'. Available: {self.config.splitting.strategies}"
            )

    def _split_study_grouped(
        self, df: pd.DataFrame, seed: int, tr_r: float, val_r: float, te_r: float
    ) -> SplitManifest:
        """Group by study_id so all variants from the same study remain in a single fold."""
        if "study_id" not in df.columns or df["study_id"].isna().all():
            # Fallback or warning if study_id is missing
            raise ValueError("Cannot perform 'study_grouped' split because 'study_id' column is missing or all null.")

        groups = df["study_id"].fillna("UNKNOWN_STUDY").astype(str).values
        unique_groups = np.unique(groups)

        if len(unique_groups) < 3:
            raise ValueError(
                f"At least 3 unique study groups are required for train/val/test grouped split, found {len(unique_groups)}."
            )

        rng = np.random.RandomState(seed)
        shuffled_groups = rng.permutation(unique_groups)

        n_groups = len(shuffled_groups)
        n_train = max(1, int(np.round(tr_r * n_groups)))
        n_val = max(1, int(np.round(val_r * n_groups)))
        if n_train + n_val >= n_groups:
            n_train = n_groups - 2
            n_val = 1

        train_grps = set(shuffled_groups[:n_train])
        val_grps = set(shuffled_groups[n_train:n_train + n_val])
        test_grps = set(shuffled_groups[n_train + n_val:])

        train_mask = df["study_id"].isin(train_grps)
        val_mask = df["study_id"].isin(val_grps)
        test_mask = df["study_id"].isin(test_grps)

        train_ids = df.loc[train_mask, "variant_id"].tolist()
        val_ids = df.loc[val_mask, "variant_id"].tolist()
        test_ids = df.loc[test_mask, "variant_id"].tolist()

        return SplitManifest(
            strategy="study_grouped",
            random_seed=seed,
            train_count=len(train_ids),
            val_count=len(val_ids),
            test_count=len(test_ids),
            train_variant_ids=train_ids,
            val_variant_ids=val_ids,
            test_variant_ids=test_ids,
            leakage_assessment=(
                "LOW LEAKAGE RISK: Full experimental studies are held out in validation and test partitions. "
                "Assay conditions and lab-specific measurement biases do not leak between train and evaluation."
            ),
            metadata={
                "train_study_groups": list(train_grps),
                "val_study_groups": list(val_grps),
                "test_study_groups": list(test_grps),
            },
        )

    def _split_parent_grouped(
        self, df: pd.DataFrame, seed: int, tr_r: float, val_r: float, te_r: float
    ) -> SplitManifest:
        """Group by parent_enzyme to evaluate homolog zero-shot transfer."""
        if "parent_enzyme" not in df.columns or df["parent_enzyme"].isna().all():
            raise ValueError("Missing 'parent_enzyme' column for parent_grouped split.")

        parents = df["parent_enzyme"].fillna("UNKNOWN_PARENT").astype(str).values
        unique_parents = np.unique(parents)

        if len(unique_parents) < 3:
            raise ValueError(
                f"At least 3 unique parent enzymes are required for parent_grouped split, found {len(unique_parents)}."
            )

        rng = np.random.RandomState(seed)
        shuffled = rng.permutation(unique_parents)
        n_p = len(shuffled)
        n_train = max(1, int(np.round(tr_r * n_p)))
        n_val = max(1, int(np.round(val_r * n_p)))
        if n_train + n_val >= n_p:
            n_train = n_p - 2
            n_val = 1

        train_p = set(shuffled[:n_train])
        val_p = set(shuffled[n_train:n_train + n_val])
        test_p = set(shuffled[n_train + n_val:])

        train_ids = df.loc[df["parent_enzyme"].isin(train_p), "variant_id"].tolist()
        val_ids = df.loc[df["parent_enzyme"].isin(val_p), "variant_id"].tolist()
        test_ids = df.loc[df["parent_enzyme"].isin(test_p), "variant_id"].tolist()

        return SplitManifest(
            strategy="parent_grouped",
            random_seed=seed,
            train_count=len(train_ids),
            val_count=len(val_ids),
            test_count=len(test_ids),
            train_variant_ids=train_ids,
            val_variant_ids=val_ids,
            test_variant_ids=test_ids,
            leakage_assessment=(
                "LOW HOMOLOGY LEAKAGE: Parent scaffolds are held out strictly between splits. "
                "Tests zero-shot generalization across distinct PET-degrading enzyme families."
            ),
            metadata={
                "train_parents": list(train_p),
                "val_parents": list(val_p),
                "test_parents": list(test_p),
            },
        )

    def _split_mutation_complexity(
        self, df: pd.DataFrame, seed: int, val_r: float, te_r: float
    ) -> SplitManifest:
        """Train on single-site mutations and WT; evaluate on multi-site combinatorial mutations."""
        mut_counts = []
        for mut_str in df.get("mutations", []):
            try:
                parsed = parse_mutations(str(mut_str) if pd.notna(mut_str) else None)
                mut_counts.append(len(parsed))
            except Exception:
                mut_counts.append(1)

        mut_arr = np.array(mut_counts)
        single_mask = mut_arr <= 1
        multi_mask = mut_arr > 1

        if not np.any(multi_mask):
            raise ValueError("No multi-site mutant variants found in dataset to create mutation_complexity evaluation split.")

        train_df = df[single_mask]
        multi_df = df[multi_mask]

        # Partition multi-mutants between validation and test
        rng = np.random.RandomState(seed)
        multi_indices = rng.permutation(len(multi_df))
        n_val = int(np.round(len(multi_df) * (val_r / (val_r + te_r))))
        n_val = max(1, min(len(multi_df) - 1, n_val))

        val_multi_idx = multi_indices[:n_val]
        test_multi_idx = multi_indices[n_val:]

        val_df = multi_df.iloc[val_multi_idx]
        test_df = multi_df.iloc[test_multi_idx]

        train_ids = train_df["variant_id"].tolist()
        val_ids = val_df["variant_id"].tolist()
        test_ids = test_df["variant_id"].tolist()

        return SplitManifest(
            strategy="mutation_complexity",
            random_seed=seed,
            train_count=len(train_ids),
            val_count=len(val_ids),
            test_count=len(test_ids),
            train_variant_ids=train_ids,
            val_variant_ids=val_ids,
            test_variant_ids=test_ids,
            leakage_assessment=(
                "TARGETED GENERALIZATION EVALUATION: Training set contains strictly single-site mutations and WT. "
                "Validation and test sets contain strictly multi-site mutations to measure higher-order epistatic modeling."
            ),
            metadata={
                "single_site_in_train": len(train_ids),
                "multi_site_in_val": len(val_ids),
                "multi_site_in_test": len(test_ids),
            },
        )

    def _split_random(
        self, df: pd.DataFrame, seed: int, tr_r: float, val_r: float, te_r: float
    ) -> SplitManifest:
        """Standard random split with clear documentation of high homology/study leakage risk."""
        n = len(df)
        rng = np.random.RandomState(seed)
        perm = rng.permutation(n)

        n_train = int(np.round(tr_r * n))
        n_val = int(np.round(val_r * n))

        train_idx = perm[:n_train]
        val_idx = perm[n_train:n_train + n_val]
        test_idx = perm[n_train + n_val:]

        train_ids = df.iloc[train_idx]["variant_id"].tolist()
        val_ids = df.iloc[val_idx]["variant_id"].tolist()
        test_ids = df.iloc[test_idx]["variant_id"].tolist()

        return SplitManifest(
            strategy="random",
            random_seed=seed,
            train_count=len(train_ids),
            val_count=len(val_ids),
            test_count=len(test_ids),
            train_variant_ids=train_ids,
            val_variant_ids=val_ids,
            test_variant_ids=test_ids,
            leakage_assessment=(
                "WARNING: HIGH DATA LEAKAGE RISK. A standard random split mixes identical sequence contexts, "
                "overlapping positional mutations, and assay-specific biases between train and test. "
                "This baseline often yields artificially inflated performance metrics."
            ),
            metadata={"random_seed": seed},
        )
