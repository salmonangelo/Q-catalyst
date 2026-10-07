"""Cached data ingestion and schema resolution for the Q-Catalyst frontend application."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st


# Crystallographic vs mature indexing dictionary (IsPETase mature 1-263 vs 5XJH crystal 28-290)
INDEXING_MAP = {
    "W132H": {"crystal_mutation": "W159H", "crystal_pos": 159, "mature_pos": 132, "role": "Substrate pocket Trp159"},
    "S133A": {"crystal_mutation": "S160A", "crystal_pos": 160, "mature_pos": 133, "role": "Catalytic nucleophile Ser160"},
    "D179A": {"crystal_mutation": "D206A", "crystal_pos": 206, "mature_pos": 179, "role": "Catalytic triad acid Asp206"},
    "H210A": {"crystal_mutation": "H237A", "crystal_pos": 237, "mature_pos": 210, "role": "Catalytic triad base His237"},
    "S133G;D179G": {"crystal_mutation": "S160G;D206G", "crystal_pos": 160, "mature_pos": 133, "role": "Double active-site mutant"},
    "WT": {"crystal_mutation": "WT", "crystal_pos": 0, "mature_pos": 0, "role": "Wild-Type Reference"},
}


@st.cache_data(show_spinner=False)
def load_latest_run_dir() -> Optional[Path]:
    """Finds the most recent valid pipeline run directory in runs/."""
    runs_dir = Path("runs")
    if not runs_dir.exists():
        return None
    run_folders = [f for f in runs_dir.iterdir() if f.is_dir() and f.name.startswith("run_")]
    if not run_folders:
        return None
    # Sort by folder name (timestamp)
    return sorted(run_folders, reverse=True)[0]


@st.cache_data(show_spinner=False)
def load_fusion_data() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Dict[str, Any], Dict[str, Any]]:
    """Loads fusion results, evidence matrix, manifest, and explanations."""
    run_dir = load_latest_run_dir()
    
    # Try loading from latest run first, fallback to fusion/
    res_path = Path("fusion/fusion_results.parquet")
    matrix_path = Path("fusion/evidence_matrix.parquet")
    manifest_path = Path("fusion/fusion_manifest.json")
    exp_path = Path("fusion/candidate_explanations.json")

    df_results = pd.read_parquet(res_path) if res_path.exists() else None
    df_matrix = pd.read_parquet(matrix_path) if matrix_path.exists() else None

    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    explanations = {}
    if exp_path.exists():
        with open(exp_path, "r", encoding="utf-8") as f:
            explanations = json.load(f)

    return df_results, df_matrix, manifest, explanations


@st.cache_data(show_spinner=False)
def load_quantum_data() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Dict[str, Any]]:
    """Loads Phase 5 quantum simulation results and VQE history."""
    run_dir = load_latest_run_dir()
    
    res_path = (run_dir / "quantum" / "quantum_results.parquet") if run_dir and (run_dir / "quantum" / "quantum_results.parquet").exists() else Path("quantum/quantum_results.parquet")
    hist_path = (run_dir / "quantum" / "vqe_history.parquet") if run_dir and (run_dir / "quantum" / "vqe_history.parquet").exists() else Path("quantum/vqe_history.parquet")
    man_path = (run_dir / "quantum" / "quantum_manifest.json") if run_dir and (run_dir / "quantum" / "quantum_manifest.json").exists() else Path("quantum/quantum_manifest.json")

    df_results = pd.read_parquet(res_path) if res_path.exists() else None
    df_hist = pd.read_parquet(hist_path) if hist_path.exists() else None

    manifest = {}
    if man_path.exists():
        with open(man_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    return df_results, df_hist, manifest


@st.cache_data(show_spinner=False)
def load_chemistry_data() -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """Loads Phase 4 classical chemistry results and cluster manifest."""
    run_dir = load_latest_run_dir()
    
    res_path = (run_dir / "chemistry" / "chem_results.parquet") if run_dir and (run_dir / "chemistry" / "chem_results.parquet").exists() else Path("chemistry/chem_results.parquet")
    rep_path = (run_dir / "chemistry" / "active_site_report.json") if run_dir and (run_dir / "chemistry" / "active_site_report.json").exists() else Path("chemistry/active_site_report.json")

    df_results = pd.read_parquet(res_path) if res_path.exists() else None

    report = {}
    if rep_path.exists():
        with open(rep_path, "r", encoding="utf-8") as f:
            report = json.load(f)

    return df_results, report


def resolve_candidate_mutation_label(mutations_str: str) -> Dict[str, Any]:
    """Resolves residue numbering between internal mature sequence and 5XJH crystal structure."""
    mut = str(mutations_str).strip()
    if mut in INDEXING_MAP:
        return INDEXING_MAP[mut]
    return {
        "crystal_mutation": mut,
        "crystal_pos": None,
        "mature_pos": None,
        "role": "Engineered Variant",
    }
