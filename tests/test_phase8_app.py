"""Unit tests for Phase 8 Streamlit frontend modules and helper functions."""

import pandas as pd
import pytest
from app.data_loader import (
    INDEXING_MAP,
    load_chemistry_data,
    load_fusion_data,
    load_latest_run_dir,
    load_quantum_data,
    resolve_candidate_mutation_label,
)
from app.charts import (
    create_candidate_ranking_chart,
    create_evidence_radar_chart,
    create_stage_durations_chart,
    create_vqe_convergence_chart,
)
from app.styles import get_custom_css


def test_styles_css_generation():
    """Verify custom CSS returns a non-empty string containing key design tokens."""
    css = get_custom_css()
    assert isinstance(css, str)
    assert "--qc-gold-primary: #C59A45" in css
    assert "--qc-bg-primary: #FAF9F6" in css
    assert "qc-brand-header" in css
    assert "qc-candidate-card" in css


def test_mutation_indexing_resolution():
    """Verify residue numbering resolution between mature sequence and 5XJH crystal structure."""
    res_w159 = resolve_candidate_mutation_label("W132H")
    assert res_w159["crystal_mutation"] == "W159H"
    assert res_w159["crystal_pos"] == 159
    assert res_w159["mature_pos"] == 132

    res_wt = resolve_candidate_mutation_label("WT")
    assert res_wt["crystal_mutation"] == "WT"

    res_unknown = resolve_candidate_mutation_label("A50G")
    assert res_unknown["crystal_mutation"] == "A50G"
    assert res_unknown["role"] == "Engineered Variant"


def test_chart_creation_radar():
    """Verify 6-axis evidence radar chart generation."""
    scores = {
        "protein_ai_score": 0.85,
        "uncertainty_quality_score": 0.72,
        "mechanism_proximity_score": 0.90,
        "chemistry_score": 0.65,
        "quantum_score": 0.95,
        "diversity_score": 0.50,
    }
    fig = create_evidence_radar_chart(scores, candidate_id="VAR_W159H", quantum_available=True)
    assert fig is not None
    assert len(fig.data) > 0
    assert fig.data[0].type == "scatterpolar"


def test_chart_creation_vqe():
    """Verify VQE convergence curve generation."""
    vqe_hist = pd.DataFrame({
        "iteration": [1, 2, 3, 4, 5],
        "energy": [-18.10, -18.15, -18.18, -18.20, -18.206475],
    })
    fig = create_vqe_convergence_chart(vqe_hist, casci_energy=-18.215733)
    assert fig is not None
    assert len(fig.data) > 0


def test_chart_creation_ranking():
    """Verify candidate ranking bar chart generation."""
    df_ranks = pd.DataFrame({
        "rank": [1, 2],
        "candidate_id": ["VAR_W159H", "VAR_WT"],
        "fusion_score": [0.7712, 0.6540],
        "decision_status": ["PRIORITIZE", "PRIORITIZE"],
    })
    fig = create_candidate_ranking_chart(df_ranks)
    assert fig is not None
    assert len(fig.data) > 0


def test_data_loader_functions():
    """Verify cached data loading functions load valid structures without error."""
    df_results, df_matrix, manifest, explanations = load_fusion_data()
    assert df_results is not None
    assert not df_results.empty
    assert "candidate_id" in df_results.columns

    df_q, df_hist, q_man = load_quantum_data()
    assert df_q is not None
    assert "variant_id" in df_q.columns

    df_c, c_rep = load_chemistry_data()
    assert df_c is not None

    latest_run = load_latest_run_dir()
    assert latest_run is not None


def test_streamlit_app_navigation():
    """Verify headless rendering of all 6 views in the Streamlit application using AppTest."""
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_path = Path("app/app.py").resolve()
    at = AppTest.from_file(str(app_path), default_timeout=30)
    at.run()
    assert not at.exception

    pages = [
        "🎯 Candidate Triage",
        "🔬 Candidate Deep-Dive",
        "⚛️ Quantum Lab",
        "🧬 Structural Mechanism",
        "⚡ Pipeline & Provenance",
    ]

    for p in pages:
        radio = at.sidebar.radio[0]
        radio.set_value(p)
        at.run()
        assert not at.exception
