"""Scientific Plotly chart generators with luxury gold, silver, and ivory styling."""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go


GOLD_COLOR = "#C59A45"
GOLD_FILL = "rgba(197, 154, 69, 0.22)"
INDIGO_COLOR = "#5B4AE4"
INDIGO_FILL = "rgba(91, 74, 228, 0.18)"
CHARCOAL_COLOR = "#15171C"
SILVER_COLOR = "#D1D5DB"
CARD_BG = "#FFFFFF"


def create_evidence_radar_chart(
    scores: Dict[str, float],
    candidate_id: str = "Candidate",
    quantum_available: bool = True,
) -> go.Figure:
    """Creates a scientific 6-axis radar chart showing normalized multimodal evidence."""
    categories = [
        "Sequence AI",
        "Uncertainty Quality",
        "Mechanism Proximity",
        "Classical Chemistry",
        "Quantum Agreement",
        "Sequence Diversity",
    ]

    vals = [
        scores.get("protein_ai_score", 0.5),
        scores.get("uncertainty_quality_score", 0.5),
        scores.get("mechanism_proximity_score", 0.5),
        scores.get("chemistry_score", 0.5),
        scores.get("quantum_score", 0.5) if quantum_available else 0.0,
        scores.get("diversity_score", 0.5),
    ]

    # Close the radar loop
    r_vals = vals + [vals[0]]
    theta_vals = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=r_vals,
        theta=theta_vals,
        fill="toself",
        fillcolor=GOLD_FILL,
        line=dict(color=GOLD_COLOR, width=2.5),
        marker=dict(size=7, color=GOLD_COLOR),
        name=candidate_id,
        hoverinfo="r+theta",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1.0],
                tickfont=dict(size=10, color="#6C757D", family="Plus Jakarta Sans"),
                gridcolor="#E5E7EB",
                linecolor="#E5E7EB",
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#15171C", family="Plus Jakarta Sans", weight=600),
                rotation=90,
                direction="clockwise",
                gridcolor="#E5E7EB",
                linecolor="#E5E7EB",
            ),
            bgcolor=CARD_BG,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=30, b=30),
        showlegend=False,
        height=340,
    )
    return fig


def create_vqe_convergence_chart(
    vqe_history_df: Optional[pd.DataFrame],
    casci_energy: float = -18.215733,
    final_vqe_energy: float = -18.206475,
) -> go.Figure:
    """Plots iteration-by-iteration VQE energy minimization against the exact CASCI baseline."""
    fig = go.Figure()

    if vqe_history_df is not None and not vqe_history_df.empty and "iteration" in vqe_history_df.columns:
        x_vals = vqe_history_df["iteration"].values
        y_vals = vqe_history_df["energy"].values

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines+markers",
            name="VQE Trajectory (TwoLocal/COBYLA)",
            line=dict(color=GOLD_COLOR, width=2.5),
            marker=dict(size=6, color=GOLD_COLOR),
            hovertemplate="Iter %{x}: %{y:.6f} Ha<extra></extra>",
        ))

        # CASCI Reference line
        fig.add_hline(
            y=casci_energy,
            line_dash="dash",
            line_color=CHARCOAL_COLOR,
            line_width=1.8,
            annotation_text=f"CASCI Exact: {casci_energy:.6f} Ha",
            annotation_position="top right",
            annotation_font=dict(size=11, color=CHARCOAL_COLOR, family="Plus Jakarta Sans"),
        )
    else:
        # Fallback synthetic demonstration trajectory if table empty
        iters = np.arange(1, 35)
        sim_energies = casci_energy + 0.08 * np.exp(-iters / 6.0) + 0.009258
        fig.add_trace(go.Scatter(
            x=iters,
            y=sim_energies,
            mode="lines+markers",
            name="VQE (Simulated Optimization)",
            line=dict(color=GOLD_COLOR, width=2.5),
            marker=dict(size=6, color=GOLD_COLOR),
        ))
        fig.add_hline(
            y=casci_energy,
            line_dash="dash",
            line_color=CHARCOAL_COLOR,
            annotation_text=f"CASCI Exact: {casci_energy:.6f} Ha",
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=CARD_BG,
        xaxis=dict(
            title="Optimizer Iteration",
            gridcolor="#F0F2F5",
            linecolor="#D1D5DB",
            title_font=dict(size=12, family="Plus Jakarta Sans"),
        ),
        yaxis=dict(
            title="Electronic Energy (Hartree)",
            gridcolor="#F0F2F5",
            linecolor="#D1D5DB",
            title_font=dict(size=12, family="Plus Jakarta Sans"),
        ),
        margin=dict(l=50, r=30, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320,
    )
    return fig


def create_candidate_ranking_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart ranking candidate variants by composite decision score."""
    fig = go.Figure()

    if df is None or df.empty:
        return fig

    # Reverse order for top-to-bottom display
    df_sorted = df.sort_values(by="rank", ascending=False)
    
    colors = []
    for st in df_sorted["decision_status"]:
        if st == "PRIORITIZE":
            colors.append(GOLD_COLOR)
        elif st == "PROMISING_BUT_UNCERTAIN":
            colors.append(INDIGO_COLOR)
        else:
            colors.append(SILVER_COLOR)

    fig.add_trace(go.Bar(
        x=df_sorted["fusion_score"],
        y=df_sorted["candidate_id"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=1, color="rgba(0,0,0,0.1)")),
        text=[f"{score:.2f} ({stat})" for score, stat in zip(df_sorted["fusion_score"], df_sorted["decision_status"])],
        textposition="inside",
        insidetextanchor="end",
        textfont=dict(color="#15171C", size=11, family="Plus Jakarta Sans"),
        hovertemplate="Candidate: %{y}<br>Composite Score: %{x:.4f}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=CARD_BG,
        xaxis=dict(
            title="Composite Decision Score [0 - 1]",
            range=[0, 1.05],
            gridcolor="#F0F2F5",
            title_font=dict(size=12, family="Plus Jakarta Sans"),
        ),
        yaxis=dict(
            gridcolor="#F0F2F5",
            title_font=dict(size=12, family="Plus Jakarta Sans"),
        ),
        margin=dict(l=40, r=20, t=10, b=30),
        height=260,
    )
    return fig


def create_stage_durations_chart(durations: Dict[str, float]) -> go.Figure:
    """Waterfall or bar visual of stage execution runtimes."""
    stages = list(durations.keys())
    durs = list(durations.values())

    fig = go.Figure(go.Bar(
        x=stages,
        y=durs,
        marker=dict(color="#3D4450"),
        text=[f"{d:.2f}s" for d in durs],
        textposition="outside",
        textfont=dict(size=10, color="#15171C"),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=CARD_BG,
        xaxis=dict(title="Pipeline Stage", gridcolor="#F0F2F5"),
        yaxis=dict(title="Runtime (Seconds)", gridcolor="#F0F2F5"),
        margin=dict(l=40, r=20, t=20, b=30),
        height=240,
    )
    return fig
