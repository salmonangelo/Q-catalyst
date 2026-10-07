"""Custom CSS and Design System for Q-Catalyst luxury scientific interface.

Visual Theme: Warm Ivory, Champagne Gold, Platinum Silver, Charcoal & Indigo Quantum Accent.
"""

def get_custom_css() -> str:
    """Returns the complete, scoped stylesheet for the Q-Catalyst application."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --qc-bg-primary: #FAF9F6;
        --qc-bg-card: #FFFFFF;
        --qc-bg-card-subtle: #F5F4F0;
        --qc-gold-primary: #C59A45;
        --qc-gold-dark: #9E7A30;
        --qc-gold-light: #DFBD74;
        --qc-gold-bg: rgba(197, 154, 69, 0.08);
        --qc-gold-border: rgba(197, 154, 69, 0.35);
        --qc-silver: #E3E5E8;
        --qc-silver-dark: #7A828E;
        --qc-charcoal-primary: #121417;
        --qc-charcoal-body: #343A40;
        --qc-charcoal-muted: #6C757D;
        --qc-quantum-accent: #5B4AE4;
        --qc-quantum-bg: rgba(91, 74, 228, 0.06);
        --qc-quantum-border: rgba(91, 74, 228, 0.25);
        --qc-success: #198754;
        --qc-success-bg: rgba(25, 135, 84, 0.08);
        --qc-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
        --qc-shadow-md: 0 6px 20px rgba(0, 0, 0, 0.06);
        --qc-shadow-lg: 0 12px 36px rgba(0, 0, 0, 0.08);
        --qc-radius-sm: 8px;
        --qc-radius-md: 14px;
        --qc-radius-lg: 20px;
    }

    /* Base Streamlit App Canvas */
    .stApp {
        background-color: var(--qc-bg-primary) !important;
        color: var(--qc-charcoal-body) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Typography */
    h1, h2, h3, .qc-display-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 700 !important;
        color: var(--qc-charcoal-primary) !important;
        letter-spacing: -0.02em !important;
    }

    .qc-serif-title {
        font-family: 'Cinzel', Georgia, serif !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }

    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1280px !important;
    }

    /* Top Brand Bar */
    .qc-brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 2rem;
        background: var(--qc-bg-card);
        border: 1px solid var(--qc-silver);
        border-radius: var(--qc-radius-md);
        box-shadow: var(--qc-shadow-sm);
        margin-bottom: 2rem;
    }

    .qc-logo-group {
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }

    .qc-logo-icon {
        width: 38px;
        height: 38px;
        background: linear-gradient(135deg, var(--qc-charcoal-primary) 0%, #2A2E35 100%);
        border: 1px solid var(--qc-gold-primary);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--qc-gold-light);
        font-family: 'Cinzel', serif;
        font-weight: 700;
        font-size: 1.15rem;
    }

    .qc-logo-text {
        font-family: 'Cinzel', serif;
        font-weight: 700;
        font-size: 1.35rem;
        color: var(--qc-charcoal-primary);
        letter-spacing: 0.08em;
    }

    .qc-badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.85rem;
        background: var(--qc-gold-bg);
        border: 1px solid var(--qc-gold-border);
        color: var(--qc-gold-dark);
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .qc-badge-quantum {
        background: var(--qc-quantum-bg);
        border-color: var(--qc-quantum-border);
        color: var(--qc-quantum-accent);
    }

    /* Hero Banner */
    .qc-hero-banner {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8F7F3 100%);
        border: 1px solid var(--qc-silver);
        border-radius: var(--qc-radius-lg);
        padding: 3.5rem 3rem;
        box-shadow: var(--qc-shadow-md);
        position: relative;
        overflow: hidden;
        margin-bottom: 2.5rem;
    }

    .qc-hero-banner::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 450px;
        height: 450px;
        background: radial-gradient(circle, rgba(197, 154, 69, 0.07) 0%, rgba(255,255,255,0) 70%);
        pointer-events: none;
    }

    .qc-hero-tag {
        color: var(--qc-gold-dark);
        font-family: 'Cinzel', serif;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }

    .qc-hero-headline {
        font-size: 2.6rem;
        line-height: 1.15;
        font-weight: 800;
        color: var(--qc-charcoal-primary);
        margin-bottom: 1.25rem;
        max-width: 820px;
    }

    .qc-hero-subhead {
        font-size: 1.15rem;
        line-height: 1.6;
        color: var(--qc-charcoal-muted);
        max-width: 720px;
        margin-bottom: 2rem;
    }

    /* Cards */
    .qc-card {
        background: var(--qc-bg-card);
        border: 1px solid var(--qc-silver);
        border-radius: var(--qc-radius-md);
        padding: 1.75rem;
        box-shadow: var(--qc-shadow-sm);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 1.25rem;
    }

    .qc-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--qc-shadow-md);
    }

    .qc-card-gold-accent {
        border-left: 4px solid var(--qc-gold-primary);
    }

    .qc-card-quantum-accent {
        border-left: 4px solid var(--qc-quantum-accent);
    }

    /* Metrics Chip */
    .qc-metric-chip {
        background: var(--qc-bg-card-subtle);
        border: 1px solid var(--qc-silver);
        border-radius: var(--qc-radius-sm);
        padding: 1rem 1.25rem;
    }

    .qc-metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--qc-charcoal-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }

    .qc-metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: var(--qc-charcoal-primary);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .qc-metric-gold {
        color: var(--qc-gold-dark);
    }

    .qc-metric-quantum {
        color: var(--qc-quantum-accent);
    }

    /* Stepper / Timeline */
    .qc-pipeline-step {
        display: flex;
        align-items: flex-start;
        gap: 1.25rem;
        padding: 1.1rem;
        background: var(--qc-bg-card);
        border: 1px solid var(--qc-silver);
        border-radius: var(--qc-radius-sm);
        margin-bottom: 0.75rem;
    }

    .qc-step-num {
        width: 32px;
        height: 32px;
        background: var(--qc-charcoal-primary);
        color: #FFFFFF;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        flex-shrink: 0;
    }

    /* Candidate Triage Card */
    .qc-candidate-card {
        background: var(--qc-bg-card);
        border: 1px solid var(--qc-silver);
        border-radius: var(--qc-radius-md);
        padding: 1.5rem;
        box-shadow: var(--qc-shadow-sm);
        margin-bottom: 1.25rem;
        position: relative;
    }

    .qc-candidate-card.qc-top-rank {
        border-color: var(--qc-gold-primary);
        box-shadow: 0 4px 18px rgba(197, 154, 69, 0.12);
        background: linear-gradient(180deg, #FFFFFF 0%, #FDFBF7 100%);
    }

    /* Explanations Box */
    .qc-explanation-box {
        background: #FDFBF7;
        border: 1px solid var(--qc-gold-border);
        border-radius: var(--qc-radius-sm);
        padding: 1.25rem;
        margin-top: 1rem;
    }

    .qc-factor-item {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        font-size: 0.9rem;
        margin-bottom: 0.4rem;
    }

    /* Footer */
    .qc-footer {
        text-align: center;
        padding: 3rem 1rem 1rem 1rem;
        color: var(--qc-charcoal-muted);
        font-size: 0.85rem;
        border-top: 1px solid var(--qc-silver);
        margin-top: 4rem;
    }
    </style>
    """
