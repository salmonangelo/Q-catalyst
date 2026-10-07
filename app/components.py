"""Reusable HTML/CSS components for the Q-Catalyst scientific interface."""

from typing import Any, Dict, List, Optional
import streamlit as st

from app.data_loader import resolve_candidate_mutation_label


def render_top_header():
    """Renders the top luxury brand bar with logo and live status badges."""
    st.markdown("""
    <div style="background: linear-gradient(90deg, rgba(197, 154, 69, 0.15) 0%, rgba(91, 74, 228, 0.08) 100%); border: 1px solid rgba(197, 154, 69, 0.35); border-radius: 8px; padding: 0.5rem 1.25rem; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem;">
        <span style="font-weight: 700; color: #7A5C1B; letter-spacing: 0.04em;">
            ⚠️ DEMO EVALUATION FIXTURE (SYNTHETIC DATA) • IN-SILICO COMPUTATIONAL SCREENING ONLY
        </span>
        <span style="color: #6C757D;">
            No Physical Hardware Advantage Claimed • Simulator: Qiskit Aer Statevector
        </span>
    </div>

    <div class="qc-brand-header">
        <div class="qc-logo-group">
            <div class="qc-logo-icon">Q</div>
            <div>
                <div class="qc-logo-text">Q-CATALYST</div>
                <div style="font-size: 0.75rem; color: #6C757D; letter-spacing: 0.05em; text-transform: uppercase;">
                    Mechanism-Aware Quantum–AI PETase Triage
                </div>
            </div>
        </div>
        <div style="display: flex; gap: 0.6rem; align-items: center;">
            <span class="qc-badge-pill">🏛️ Hybrid Prototype</span>
            <span class="qc-badge-pill qc-badge-quantum">⚛️ Qiskit (4e, 4o / 8Q)</span>
            <span class="qc-badge-pill" style="background: rgba(0,0,0,0.04); color: #495057; border-color: #CED4DA;">
                🧬 PDB: 5XJH (1.58 Å)
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hero():
    """Renders the editorial hero section with high-level value proposition."""
    st.markdown("""
    <div class="qc-hero-banner">
        <div class="qc-hero-tag">National Quantum Hackathon Prototype • 2026</div>
        <h1 class="qc-hero-headline">
            Mechanism-Aware Quantum–AI Triage for PETase Engineering
        </h1>
        <p class="qc-hero-subhead">
            Accelerating biocatalytic plastic degradation by bridging sequence-level protein AI, structural catalytic reasoning, and active-space quantum chemical simulation into a transparent candidate decision engine.
        </p>
        <div style="display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
            <div style="background: #15171C; color: #FFFFFF; padding: 0.65rem 1.4rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 0.5rem;">
                🎯 6 Multimodal Evidence Channels
            </div>
            <div style="background: rgba(197, 154, 69, 0.12); color: #9E7A30; border: 1px solid rgba(197, 154, 69, 0.35); padding: 0.65rem 1.4rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;">
                ⚛️ Statevector / Aer 8-Qubit VQE
            </div>
            <div style="background: rgba(0,0,0,0.04); color: #495057; border: 1px solid #CED4DA; padding: 0.65rem 1.4rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;">
                🔬 Catalytic Pocket: Ser160 • Asp206 • His237
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_candidate_card(row: Dict[str, Any], rank: int, is_top: bool = False):
    """Renders a candidate triage summary card with decision pill, coverage, and mutation metadata."""
    cid = row.get("candidate_id", "Unknown")
    muts = row.get("mutations", "WT")
    score = row.get("fusion_score", 0.0)
    status = row.get("decision_status", "UNKNOWN")
    coverage = row.get("evidence_coverage", row.get("evidence_coverage_score", "N/A"))
    if isinstance(coverage, float):
        coverage = f"{int(coverage * 6)}/6"

    conf = row.get("confidence_label", "MODERATE_CONFIDENCE")
    vqe_err = row.get("vqe_casci_error")
    
    # Resolve residue numbering mapping
    indexing = resolve_candidate_mutation_label(muts)
    crystal_note = f"Crystal (5XJH): <b>{indexing['crystal_mutation']}</b> ({indexing['role']})" if indexing['crystal_pos'] else f"{indexing['role']}"

    top_class = "qc-top-rank" if is_top else ""
    status_bg = "#EAF8EE" if status == "PRIORITIZE" else ("#EEF2FF" if status == "PROMISING_BUT_UNCERTAIN" else "#F3F4F6")
    status_color = "#1E7E34" if status == "PRIORITIZE" else ("#4338CA" if status == "PROMISING_BUT_UNCERTAIN" else "#6B7280")
    
    qm_badge = (
        f"<span style='background: rgba(197, 154, 69, 0.1); color: #9E7A30; border: 1px solid rgba(197, 154, 69, 0.3); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>⚛️ VQE Error: {vqe_err:.4f} Ha</span>"
        if vqe_err is not None
        else "<span style='background: #F3F4F6; color: #9CA3AF; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;'>Quantum: Not Simulated</span>"
    )

    st.markdown(f"""
    <div class="qc-candidate-card {top_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div>
                <span style="font-family: 'Cinzel', serif; font-weight: 700; font-size: 1.1rem; color: #C59A45; margin-right: 0.5rem;">
                    #{rank:02d}
                </span>
                <span style="font-size: 1.15rem; font-weight: 700; color: #15171C;">
                    {cid}
                </span>
                <div style="font-size: 0.8rem; color: #6C757D; margin-top: 0.2rem;">
                    {crystal_note}
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: {status_bg}; color: {status_color}; padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.04em;">
                    {status}
                </span>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; background: #FAF9F6; padding: 0.85rem; border-radius: 8px; border: 1px solid #E5E7EB; margin-bottom: 0.75rem;">
            <div>
                <div style="font-size: 0.7rem; color: #6C757D; text-transform: uppercase;">Composite Score</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #15171C;">{score:.4f}</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #6C757D; text-transform: uppercase;">Evidence Coverage</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #15171C;">{coverage} Channels</div>
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #6C757D; text-transform: uppercase;">Confidence Tier</div>
                <div style="font-size: 0.95rem; font-weight: 600; color: #374151;">{conf}</div>
            </div>
        </div>

        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>{qm_badge}</div>
            <span style="font-size: 0.75rem; color: #6B7280; font-style: italic;">
                Synthetic Fixture Provenance Preserved
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_why_candidate_box(explanation: Dict[str, Any]):
    """Renders the deterministic rule-based natural language explainability card."""
    if not explanation:
        return

    summary = explanation.get("summary", "No structured summary available.")
    positives = explanation.get("positive_factors", [])
    negatives = explanation.get("negative_factors", [])
    missing = explanation.get("missing_evidence", [])
    limitations = explanation.get("limitations", [])

    st.markdown(f"""
    <div class="qc-explanation-box">
        <div style="font-family: 'Cinzel', serif; font-weight: 700; font-size: 0.95rem; color: #9E7A30; margin-bottom: 0.5rem;">
            💡 WHY THIS CANDIDATE WAS PRIORITIZED
        </div>
        <p style="font-size: 0.95rem; line-height: 1.5; color: #15171C; margin-bottom: 0.85rem;">
            {summary}
        </p>
    """, unsafe_allow_html=True)

    if positives:
        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #1E7E34; margin-bottom: 0.25rem;'>SUPPORTING EVIDENCE:</div>", unsafe_allow_html=True)
        for p in positives:
            st.markdown(f"<div class='qc-factor-item'><span style='color: #1E7E34;'>✓</span> <span>{p}</span></div>", unsafe_allow_html=True)

    if negatives:
        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #DC3545; margin-top: 0.5rem; margin-bottom: 0.25rem;'>CAUTIONARY FACTORS:</div>", unsafe_allow_html=True)
        for n in negatives:
            st.markdown(f"<div class='qc-factor-item'><span style='color: #DC3545;'>△</span> <span>{n}</span></div>", unsafe_allow_html=True)

    if missing:
        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #6C757D; margin-top: 0.5rem; margin-bottom: 0.25rem;'>UNCOMPUTED CHANNELS:</div>", unsafe_allow_html=True)
        for m in missing:
            st.markdown(f"<div class='qc-factor-item'><span style='color: #6C757D;'>•</span> <span>{m}</span></div>", unsafe_allow_html=True)

    if limitations:
        st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #9E7A30; margin-top: 0.5rem; margin-bottom: 0.25rem;'>SCIENTIFIC LIMITATIONS:</div>", unsafe_allow_html=True)
        for l in limitations:
            st.markdown(f"<div class='qc-factor-item'><span style='color: #9E7A30;'>ℹ</span> <span>{l}</span></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_footer():
    """Renders the consistent project footer."""
    st.markdown("""
    <div class="qc-footer">
        <div style="font-family: 'Cinzel', serif; font-weight: 700; font-size: 1rem; color: #15171C; margin-bottom: 0.4rem;">
            Q-CATALYST
        </div>
        <div style="font-size: 0.85rem; color: #6C757D; max-width: 680px; margin: 0 auto 1rem auto;">
            Mechanism-Aware Quantum–AI Triage for PETase Engineering • Hybrid Quantum-Classical Prototype
        </div>
        <div style="display: flex; gap: 1.5rem; justify-content: center; font-size: 0.8rem; font-weight: 600; color: #9E7A30;">
            <span>PDB: 5XJH</span>
            <span>•</span>
            <span>Qiskit Statevector Simulator</span>
            <span>•</span>
            <span>Classical Active-Space Model</span>
            <span>•</span>
            <span>Computational Triage Only</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
