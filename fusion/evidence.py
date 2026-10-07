"""Evidence extraction, cross-module aggregation, and candidate profiling."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import numpy as np
import pandas as pd

from fusion.config import FusionConfig
from fusion.normalize import EvidenceNormalizer, NormalizedFeature


@dataclass
class CandidateEvidenceProfile:
    """Consolidated multimodal evidence profile for a single engineered enzyme candidate."""
    candidate_id: str
    mutations: str
    parent_enzyme: str

    # Normalized evidence channels [0, 1]
    protein_ai_feature: NormalizedFeature
    uncertainty_feature: NormalizedFeature
    mechanism_feature: NormalizedFeature
    chemistry_feature: NormalizedFeature
    quantum_feature: NormalizedFeature
    diversity_feature: NormalizedFeature

    # Backend and provenance metadata
    quantum_backend_type: str = "SIMULATOR"
    integral_backend: str = "CLASSICAL_FALLBACK"
    vqe_casci_error: Optional[float] = None
    synthetic_data_present: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def protein_ai_score(self) -> float:
        return self.protein_ai_feature.normalized_value

    @property
    def uncertainty_quality_score(self) -> float:
        return self.uncertainty_feature.normalized_value

    @property
    def mechanism_proximity_score(self) -> float:
        return self.mechanism_feature.normalized_value

    @property
    def chemistry_score(self) -> float:
        return self.chemistry_feature.normalized_value

    @property
    def quantum_score(self) -> float:
        return self.quantum_feature.normalized_value

    @property
    def diversity_score(self) -> float:
        return self.diversity_feature.normalized_value

    @property
    def available_channels(self) -> List[str]:
        channels = []
        if self.protein_ai_feature.available:
            channels.append("protein_ai")
        if self.uncertainty_feature.available:
            channels.append("uncertainty")
        if self.mechanism_feature.available:
            channels.append("mechanism")
        if self.chemistry_feature.available:
            channels.append("chemistry")
        if self.quantum_feature.available:
            channels.append("quantum")
        if self.diversity_feature.available:
            channels.append("diversity")
        return channels

    @property
    def missing_channels(self) -> List[str]:
        all_ch = ["protein_ai", "uncertainty", "mechanism", "chemistry", "quantum", "diversity"]
        avail = set(self.available_channels)
        return [c for c in all_ch if c not in avail]

    @property
    def evidence_coverage_score(self) -> float:
        """Fraction of expected evidence channels (out of 6) that are available."""
        return len(self.available_channels) / 6.0


class EvidenceAggregator:
    """Extracts, joins, and normalizes evidence from all upstream pipeline artifacts."""

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
        self.normalizer = EvidenceNormalizer()

    def _safe_read_parquet(self, path: Path | str) -> Optional[pd.DataFrame]:
        p = Path(path)
        if not p.exists():
            return None
        try:
            return pd.read_parquet(p)
        except Exception:
            return None

    def aggregate_evidence(
        self,
        protein_ai_df: Optional[pd.DataFrame] = None,
        uncertainty_df: Optional[pd.DataFrame] = None,
        acquisition_df: Optional[pd.DataFrame] = None,
        chemistry_df: Optional[pd.DataFrame] = None,
        quantum_df: Optional[pd.DataFrame] = None,
    ) -> List[CandidateEvidenceProfile]:
        """Loads and joins multimodal evidence into unified CandidateEvidenceProfiles."""
        # Read files if DataFrames are not explicitly provided
        df_ai = protein_ai_df if protein_ai_df is not None else self._safe_read_parquet(self.config.protein_ai_path)
        df_unc = uncertainty_df if uncertainty_df is not None else self._safe_read_parquet(self.config.uncertainty_path)
        df_acq = acquisition_df if acquisition_df is not None else self._safe_read_parquet(self.config.acquisition_path)
        df_chem = chemistry_df if chemistry_df is not None else self._safe_read_parquet(self.config.chemistry_path)
        df_qm = quantum_df if quantum_df is not None else self._safe_read_parquet(self.config.quantum_path)

        # Collect unique candidate identifiers
        candidate_ids: Set[str] = set()
        for df in (df_ai, df_unc, df_acq, df_chem, df_qm):
            if df is not None:
                for col in ("variant_id", "candidate_id", "job_id"):
                    if col in df.columns:
                        candidate_ids.update(df[col].dropna().astype(str).unique())
                        break

        # If empty, return empty list
        if not candidate_ids:
            return []

        # Index DataFrames by candidate_id for O(1) lookup
        def make_lookup(df: Optional[pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
            if df is None:
                return {}
            lookup = {}
            id_col = next((c for c in ("variant_id", "candidate_id", "job_id") if c in df.columns), None)
            if not id_col:
                return {}
            for _, row in df.iterrows():
                cid = str(row[id_col])
                lookup[cid] = row.to_dict()
            return lookup

        ai_map = make_lookup(df_ai)
        unc_map = make_lookup(df_unc)
        acq_map = make_lookup(df_acq)
        chem_map = make_lookup(df_chem)
        qm_map = make_lookup(df_qm)

        profiles: List[CandidateEvidenceProfile] = []

        # Sort candidate IDs for reproducibility
        for cid in sorted(list(candidate_ids)):
            ai_data = ai_map.get(cid, {})
            unc_data = unc_map.get(cid, {})
            acq_data = acq_map.get(cid, {})
            chem_data = chem_map.get(cid, {})
            qm_data = qm_map.get(cid, {})

            # Identify general metadata
            mutations = str(
                chem_data.get("mutations")
                or acq_data.get("mutations")
                or ai_data.get("mutations")
                or "WT"
            )
            parent = str(
                chem_data.get("parent_enzyme")
                or acq_data.get("parent_enzyme")
                or "IsPETase"
            )

            # Check synthetic provenance across modules
            is_synthetic = any(
                "synthetic" in str(d.get("data_source", "")).lower()
                or "synthetic" in str(d.get("data_quality_flag", "")).lower()
                for d in (ai_data, unc_data, acq_data, chem_data, qm_data)
            )

            # 1. Protein-AI feature
            pred_val = ai_data.get("prediction") or acq_data.get("predicted_performance")
            ai_feat = self.normalizer.normalize_protein_ai(
                candidate_id=cid,
                raw_prediction=pred_val,
                synthetic=is_synthetic,
            )

            # 2. Uncertainty feature
            unc_val = unc_data.get("uncertainty_score") or unc_data.get("ensemble_std")
            unc_feat = self.normalizer.normalize_uncertainty_quality(
                candidate_id=cid,
                raw_uncertainty=unc_val,
                synthetic=is_synthetic,
            )

            # 3. Mechanism proximity feature
            prox_val = acq_data.get("acquisition_score") or acq_data.get("proximity_score")
            dist_val = chem_data.get("min_mutation_distance_to_active_site")
            mech_feat = self.normalizer.normalize_mechanism_proximity(
                candidate_id=cid,
                raw_proximity=prox_val,
                min_distance_angstrom=dist_val,
                synthetic=is_synthetic,
            )

            # 4. Chemistry feature
            geom_status = chem_data.get("geometry_status", "valid") if chem_data else None
            scf_conv = chem_data.get("scf_converged", True) if chem_data else None
            delta_e = chem_data.get("delta_energy") if chem_data else None
            calc_status = chem_data.get("calculation_status", "COMPLETED") if chem_data else "MISSING"

            chem_feat = self.normalizer.normalize_chemistry_evidence(
                candidate_id=cid,
                geometry_status=geom_status,
                scf_converged=scf_conv,
                delta_energy=delta_e,
                calculation_status=calc_status,
                synthetic=is_synthetic,
            )

            # 5. Quantum feature
            vqe_err = qm_data.get("vqe_absolute_error")
            if vqe_err is None and "vqe_energy" in qm_data and "casci_energy" in qm_data:
                try:
                    vqe_err = abs(float(qm_data["vqe_energy"]) - float(qm_data["casci_energy"]))
                except Exception:
                    vqe_err = None

            qm_feat = self.normalizer.normalize_quantum_evidence(
                candidate_id=cid,
                vqe_casci_error=vqe_err,
                vqe_converged=bool(qm_data.get("calculation_status") == "COMPLETED") if qm_data else True,
                synthetic=is_synthetic,
            )

            # 6. Diversity feature
            div_val = acq_data.get("diversity_score") or (0.8 if acq_data else None)
            div_feat = self.normalizer.normalize_diversity(
                candidate_id=cid,
                raw_diversity=div_val,
                synthetic=is_synthetic,
            )

            # Determine backends
            integral_backend = "CLASSICAL_FALLBACK"
            if chem_data and chem_data.get("method") == "HF" and "pyscf" in str(chem_data.get("data_source", "")).lower():
                integral_backend = "PYSCF"

            profiles.append(
                CandidateEvidenceProfile(
                    candidate_id=cid,
                    mutations=mutations,
                    parent_enzyme=parent,
                    protein_ai_feature=ai_feat,
                    uncertainty_feature=unc_feat,
                    mechanism_feature=mech_feat,
                    chemistry_feature=chem_feat,
                    quantum_feature=qm_feat,
                    diversity_feature=div_feat,
                    quantum_backend_type="SIMULATOR",
                    integral_backend=integral_backend,
                    vqe_casci_error=float(vqe_err) if vqe_err is not None else None,
                    synthetic_data_present=is_synthetic,
                    metadata={
                        "raw_ai_data": ai_data,
                        "raw_chem_data": chem_data,
                        "raw_qm_data": qm_data,
                    },
                )
            )

        return profiles
