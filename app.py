
from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy.stats import norm


# ============================================================
# IDLE LOOP OBSERVATORY — GAMING COMMAND CENTER
# ============================================================

ROOT = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT / "data" / "external" / "flood_it"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports" / "public_data"

DAILY_FILE = PUBLIC_DIR / "04_daily_retention.csv"
SUMMARY_FILE = PUBLIC_DIR / "05_retention_summary.csv"
EVENT_QUALITY_FILE = PUBLIC_DIR / "03_event_quality_by_day.csv"
DATE_COVERAGE_FILE = PUBLIC_DIR / "02_date_coverage.csv"

QUALITY_FILE = REPORT_DIR / "flood_it_validation_report.txt"
FINDINGS_FILE = REPORT_DIR / "flood_it_retention_findings.md"

SYNTHETIC_METRICS_FILE = PROCESSED_DIR / "synthetic_experiment_metrics.csv"
SYNTHETIC_SRM_FILE = PROCESSED_DIR / "synthetic_experiment_srm.json"
SYNTHETIC_REPORT_FILE = PROCESSED_DIR / "synthetic_experiment_readiness.md"
SYNTHETIC_COHORT_FILE = PROCESSED_DIR / "synthetic_player_cohort.csv"

st.set_page_config(
    page_title="Idle Loop // Game Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GAMING VISUAL SYSTEM
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Rajdhani:wght@400;500;600;700&display=swap');

    :root {
        --bg: #080b16;
        --panel: #11182b;
        --panel2: #17213a;
        --border: #334667;
        --cyan: #4dfcff;
        --purple: #b18cff;
        --pink: #ff62ca;
        --green: #66ffb7;
        --yellow: #ffe27a;
        --text: #f3f6ff;
        --muted: #bac8e1;
    }

    html, body, [class*="css"] {
        font-family: 'Rajdhani', sans-serif;
        font-size: 17px;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background:
            radial-gradient(ellipse at 10% 0%, rgba(92, 61, 185, .16), transparent 34%),
            radial-gradient(ellipse at 90% 20%, rgba(0, 220, 255, .08), transparent 32%),
            var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(8, 11, 22, .95);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #11182c 0%, #090d18 100%);
        border-right: 1px solid #334667;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: var(--text);
    }

    h1, h2, h3, h4 {
        font-family: 'Orbitron', sans-serif !important;
        color: #f4f7ff !important;
        letter-spacing: .01em;
    }

    p, li, label {
        color: #e0e8f8;
    }

    [data-testid="stCaptionContainer"],
    .stCaption {
        color: var(--muted) !important;
    }

    .game-hero {
        position: relative;
        overflow: hidden;
        padding: 2rem;
        border: 1px solid #3b5079;
        border-radius: 7px;
        background:
            linear-gradient(110deg, rgba(22, 34, 65, .98), rgba(13, 20, 40, .97));
        box-shadow: 0 0 32px rgba(77, 252, 255, .06),
                    inset 0 0 36px rgba(177, 140, 255, .06);
        margin-bottom: 1.5rem;
    }

    .game-hero:after {
        content: "";
        position: absolute;
        right: -65px;
        top: -105px;
        width: 260px;
        height: 260px;
        border: 1px solid rgba(77, 252, 255, .3);
        transform: rotate(45deg);
        box-shadow: 0 0 0 24px rgba(77, 252, 255, .025),
                    0 0 0 48px rgba(177, 140, 255, .025);
        pointer-events: none;
    }

    .hero-eyebrow {
        color: var(--cyan);
        font-family: 'Orbitron', sans-serif;
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: .2em;
        text-transform: uppercase;
    }

    .hero-title {
        position: relative;
        z-index: 1;
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(1.6rem, 3vw, 2.8rem);
        font-weight: 900;
        line-height: 1.25;
        margin: .7rem 0;
        color: #ffffff;
        text-shadow: 0 0 24px rgba(77, 252, 255, .25);
    }

    .hero-copy {
        position: relative;
        z-index: 1;
        max-width: 780px;
        font-size: 1.05rem;
        line-height: 1.65;
        color: #d6e2f8;
    }

    .hero-tags {
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin-top: 1.2rem;
        position: relative;
        z-index: 1;
    }

    .hero-tag {
        border: 1px solid #425779;
        border-radius: 3px;
        background: #121e36;
        color: #c7d9ff;
        padding: .35rem .65rem;
        font-family: 'Orbitron', sans-serif;
        font-size: .62rem;
        letter-spacing: .08em;
    }

    .section-kicker {
        color: var(--pink);
        font-family: 'Orbitron', sans-serif;
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: .17em;
        text-transform: uppercase;
        margin-bottom: .5rem;
    }

    .mission-banner {
        padding: .85rem 1rem;
        background: linear-gradient(90deg, #191e3c, #131a2d);
        border: 1px solid #384469;
        border-left: 4px solid var(--purple);
        border-radius: 4px;
        color: #e4eaff;
        margin: .7rem 0 1.1rem;
        line-height: 1.6;
    }

    .metric-card {
        position: relative;
        overflow: hidden;
        padding: 1.15rem 1.15rem 1rem;
        min-height: 137px;
        border: 1px solid #344969;
        border-radius: 5px;
        background: linear-gradient(145deg, #17213a, #0e1425);
        box-shadow: 0 5px 22px rgba(0, 0, 0, .2);
    }

    .metric-card:before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background: var(--cyan);
        box-shadow: 0 0 12px var(--cyan);
    }

    .metric-label {
        color: #c1cde8;
        font-family: 'Orbitron', sans-serif;
        font-size: .64rem;
        line-height: 1.6;
        letter-spacing: .08em;
        font-weight: 700;
        margin-bottom: .65rem;
    }

    .metric-value {
        color: var(--cyan);
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(1.3rem, 2vw, 1.95rem);
        line-height: 1.3;
        font-weight: 800;
        overflow-wrap: anywhere;
        text-shadow: 0 0 15px rgba(77, 252, 255, .15);
    }

    .metric-caption {
        color: #c4d0e6;
        font-size: .84rem;
        line-height: 1.45;
        margin-top: .55rem;
    }

    .source-note {
        padding: .95rem 1.1rem;
        margin: .8rem 0 1.1rem;
        color: #e2eaff;
        background: #141e34;
        border: 1px solid #3b4d70;
        border-left: 4px solid var(--purple);
        border-radius: 4px;
        line-height: 1.65;
    }

    .status-pass {
        padding: .8rem 1rem;
        color: #aaffd7;
        background: #102c29;
        border: 1px solid #2f846a;
        border-radius: 4px;
        font-weight: 700;
    }

    .status-warning {
        padding: .8rem 1rem;
        color: #ffe7a6;
        background: #342815;
        border: 1px solid #8c6b36;
        border-radius: 4px;
        font-weight: 700;
    }

    .mission-card {
        min-height: 150px;
        padding: 1.1rem;
        border: 1px solid #344969;
        border-radius: 5px;
        background: linear-gradient(145deg, #17213a, #0e1425);
    }

    .mission-icon {
        font-size: 1.7rem;
        margin-bottom: .5rem;
    }

    .mission-title {
        font-family: 'Orbitron', sans-serif;
        font-size: .8rem;
        color: var(--cyan);
        letter-spacing: .04em;
        font-weight: 700;
        margin-bottom: .5rem;
    }

    .mission-copy {
        font-size: .9rem;
        color: #c5d1e7;
        line-height: 1.55;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #344969;
        border-radius: 5px;
        overflow: hidden;
    }

    [data-testid="stJson"] {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 5px;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background: #17223b;
        border-color: #53698f;
    }

    div[data-baseweb="select"] *,
    div[data-baseweb="input"] input {
        color: #ffffff;
    }

    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button {
        border: 1px solid var(--cyan);
        border-radius: 3px;
        background: #132b3b;
        color: #efffff;
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        transition: .2s ease;
    }

    div[data-testid="stButton"] button:hover,
    div[data-testid="stDownloadButton"] button:hover {
        border-color: var(--pink);
        box-shadow: 0 0 15px rgba(255, 98, 202, .2);
    }

    [data-testid="stAlert"] {
        border-radius: 4px;
    }

    hr {
        border-color: #2d3e60;
    }

    .footer {
        color: #bac8e1;
        font-family: 'Orbitron', sans-serif;
        font-size: .65rem;
        letter-spacing: .05em;
        line-height: 1.9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Chart theme
# ============================================================

PLOT_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Rajdhani, sans-serif", "color": "#e7efff", "size": 14},
    "margin": {"l": 18, "r": 20, "t": 60, "b": 20},
    "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02},
    "hoverlabel": {
        "bgcolor": "#17213a",
        "font_color": "#ffffff",
        "bordercolor": "#4dfcff",
    },
}


# ============================================================
# Data loaders
# ============================================================

@st.cache_data
def load_csv(path_string):
    path = Path(path_string)
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return None


@st.cache_data
def load_text(path_string):
    path = Path(path_string)
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


@st.cache_data
def load_json(path_string):
    path = Path(path_string)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


daily_raw = load_csv(str(DAILY_FILE))
summary_raw = load_csv(str(SUMMARY_FILE))
event_quality = load_csv(str(EVENT_QUALITY_FILE))
date_coverage = load_csv(str(DATE_COVERAGE_FILE))

quality_text = load_text(str(QUALITY_FILE))
findings_text = load_text(str(FINDINGS_FILE))
synthetic_report = load_text(str(SYNTHETIC_REPORT_FILE))

synthetic_metrics = load_csv(str(SYNTHETIC_METRICS_FILE))
synthetic_cohort = load_csv(str(SYNTHETIC_COHORT_FILE))
srm_result = load_json(str(SYNTHETIC_SRM_FILE))


# ============================================================
# Data preparation
# ============================================================

def missing_columns(frame, required):
    if frame is None:
        return list(required)
    return [col for col in required if col not in frame.columns]


def prepare_public_data(daily_frame, summary_frame):
    required_daily = [
        "cohort_date",
        "platform",
        "cohort_users",
        "d1_retained_users",
        "d1_retention_pct",
        "d7_retained_users",
        "d7_retention_pct",
    ]

    required_summary = [
        "platform",
        "cohort_users",
        "d1_users",
        "d1_retention_pct",
        "d1_ci_lower_pct",
        "d1_ci_upper_pct",
        "d7_users",
        "d7_retention_pct",
        "d7_ci_lower_pct",
        "d7_ci_upper_pct",
    ]

    d_missing = missing_columns(daily_frame, required_daily)
    s_missing = missing_columns(summary_frame, required_summary)

    if d_missing or s_missing:
        return None, None, d_missing, s_missing

    d = daily_frame.copy()
    s = summary_frame.copy()

    d["cohort_date"] = pd.to_datetime(d["cohort_date"], errors="coerce")
    d["platform"] = d["platform"].astype("string").str.strip().str.upper()
    s["platform"] = s["platform"].astype("string").str.strip().str.upper()

    for col in [
        "cohort_users",
        "d1_retained_users",
        "d1_retention_pct",
        "d7_retained_users",
        "d7_retention_pct",
    ]:
        d[col] = pd.to_numeric(d[col], errors="coerce")

    for col in [
        "cohort_users",
        "d1_users",
        "d1_retention_pct",
        "d1_ci_lower_pct",
        "d1_ci_upper_pct",
        "d7_users",
        "d7_retention_pct",
        "d7_ci_lower_pct",
        "d7_ci_upper_pct",
    ]:
        s[col] = pd.to_numeric(s[col], errors="coerce")

    d = d.dropna(
        subset=[
            "cohort_date",
            "platform",
            "cohort_users",
            "d1_retained_users",
            "d7_retained_users",
        ]
    )
    s = s.dropna(
        subset=[
            "platform",
            "cohort_users",
            "d1_retention_pct",
            "d7_retention_pct",
        ]
    )

    return d, s, [], []


public_daily, public_summary, daily_missing, summary_missing = prepare_public_data(
    daily_raw, summary_raw
)


# ============================================================
# Reusable UI helpers
# ============================================================

def metric_card(label, value, caption=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">◈ {label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pooled_summary(frame):
    if frame is None or frame.empty:
        return None
    rows = frame[
        frame["platform"].astype(str).str.upper().isin(
            ["ALL_PLATFORMS", "ALL PLATFORMS", "ALL"]
        )
    ]
    return rows.iloc[0] if not rows.empty else None


def platform_summary(frame):
    if frame is None or frame.empty:
        return pd.DataFrame()
    return frame[
        ~frame["platform"].astype(str).str.upper().isin(
            ["ALL_PLATFORMS", "ALL PLATFORMS", "ALL"]
        )
    ].copy()


def weighted_retention(frame, retained_col):
    denominator = frame["cohort_users"].sum()
    if denominator <= 0:
        return np.nan
    return 100 * frame[retained_col].sum() / denominator


def validation_status(report_text):
    if not report_text:
        return False
    return all(
        text in report_text
        for text in ["Files checked: 5", "Errors: 0", "Warnings: 0"]
    )


def show_table(frame):
    if frame is None or frame.empty:
        st.info("No records are available for this view.")
    else:
        st.dataframe(frame, use_container_width=True, hide_index=True)


def section_header(kicker, title, description):
    st.markdown(
        f'<div class="section-kicker">{kicker}</div>',
        unsafe_allow_html=True,
    )
    st.header(title)
    st.write(description)


# ============================================================
# SIDEBAR — MISSION SELECT
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="
            padding:1rem 0 1.1rem;
            border-bottom:1px solid #334667;
            margin-bottom:1.2rem;
        ">
            <div style="font-size:2.4rem;">🎮</div>
            <div style="
                font-family:Orbitron,sans-serif;
                font-size:1.05rem;
                font-weight:900;
                color:#4dfcff;
                letter-spacing:.07em;
            ">IDLE LOOP</div>
            <div style="
                font-size:.72rem;
                letter-spacing:.17em;
                color:#bac8e1;
                margin-top:.3rem;
            ">ANALYTICS COMMAND</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🕹️ MISSION SELECT")

    page = st.radio(
        "Workspace",
        [
            "Overview",
            "Retention Explorer",
            "Experiment Lab",
            "Data Quality",
        ],
        label_visibility="collapsed",
        format_func=lambda item: {
            "Overview": "🌌  Command Center",
            "Retention Explorer": "📊  Player Observatory",
            "Experiment Lab": "⚔️  Experiment Arena",
            "Data Quality": "🛡️  Data Integrity",
        }[item],
    )

    st.divider()
    st.markdown("#### 📡 ACTIVE DATA SOURCE")
    st.markdown("**FLOOD-IT! / 2018**")
    st.caption("Public Firebase / Google Analytics sample")

    st.warning(
        "Flood-It! is not an idle game and this is not Kolibri Games data.",
        icon="⚠️",
    )

    st.divider()
    st.markdown("#### ⚙️ SYSTEM STATUS")
    st.markdown("🟢 Analytics pipeline")
    st.markdown("🟢 Statistical checks")
    st.markdown("🟢 Provenance controls")
    st.markdown("🔵 Local UI prototype")


# ============================================================
# GLOBAL GAME HEADER
# ============================================================

st.markdown(
    """
    <div class="game-hero">
        <div class="hero-eyebrow">SYSTEM ONLINE // PLAYER INTELLIGENCE DIVISION</div>
        <div class="hero-title">IDLE LOOP<br>OBSERVATORY</div>
        <div class="hero-copy">
            Your mission: turn player events into actionable retention insights.
            Explore cohorts, investigate engagement patterns, and evaluate
            experiment readiness in a game-inspired analytics command center.
        </div>
        <div class="hero-tags">
            <span class="hero-tag">PLAYER INTELLIGENCE</span>
            <span class="hero-tag">RETENTION ANALYTICS</span>
            <span class="hero-tag">EXPERIMENT PROTOCOL</span>
            <span class="hero-tag">DATA INTEGRITY</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PAGE 1 — COMMAND CENTER
# ============================================================

if page == "Overview":
    section_header(
        "MISSION 01 // COMMAND CENTER",
        "Player intelligence overview",
        "A high-level view of the historical public sample and its retention metrics.",
    )

    pooled = pooled_summary(public_summary)

    if pooled is None:
        st.error(
            "The pooled summary could not be loaded. Check the summary CSV "
            "and required column names."
        )
        if summary_missing:
            st.write("Missing columns:", summary_missing)
    else:
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            metric_card(
                "COHORT PLAYERS",
                f"{int(pooled['cohort_users']):,}",
                "Eligible observed users",
            )
        with c2:
            metric_card(
                "D1 RETENTION",
                f"{pooled['d1_retention_pct']:.2f}%",
                f"{int(pooled['d1_users']):,} returned on day 1",
            )
        with c3:
            metric_card(
                "D7 RETENTION",
                f"{pooled['d7_retention_pct']:.2f}%",
                f"{int(pooled['d7_users']):,} returned on day 7",
            )
        with c4:
            platform_rows = platform_summary(public_summary)
            metric_card(
                "PLATFORMS",
                str(platform_rows["platform"].nunique()),
                "Available platform segments",
            )

        st.markdown(
            """
            <div class="source-note">
                <strong>⚠ DATA INTEL:</strong> These metrics come from the public
                historical Flood-It! sample. Flood-It! is not an idle game.
                The results are not benchmarks for Kolibri Games and do not
                represent its players.
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)

        with left:
            st.subheader("⚡ PLATFORM BATTLE")
            platform_rows = platform_summary(public_summary)

            if not platform_rows.empty:
                long_data = platform_rows.melt(
                    id_vars=["platform"],
                    value_vars=["d1_retention_pct", "d7_retention_pct"],
                    var_name="metric",
                    value_name="retention",
                )
                long_data["metric"] = long_data["metric"].map(
                    {
                        "d1_retention_pct": "D1",
                        "d7_retention_pct": "D7",
                    }
                )

                fig = px.bar(
                    long_data,
                    x="platform",
                    y="retention",
                    color="metric",
                    barmode="group",
                    text="retention",
                    color_discrete_map={"D1": "#4dfcff", "D7": "#b18cff"},
                    labels={
                        "platform": "Platform",
                        "retention": "Retention (%)",
                        "metric": "Checkpoint",
                    },
                )
                fig.update_traces(
                    texttemplate="%{y:.2f}%",
                    textposition="outside",
                    cliponaxis=False,
                )
                fig.update_layout(
                    title="Retention checkpoint comparison",
                    yaxis_title="Retention (%)",
                    **PLOT_LAYOUT,
                )
                st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("🛡️ STATISTICAL SHIELD")
            labels = ["D1", "D7"]
            values = [
                pooled["d1_retention_pct"],
                pooled["d7_retention_pct"],
            ]
            lower = [
                values[0] - pooled["d1_ci_lower_pct"],
                values[1] - pooled["d7_ci_lower_pct"],
            ]
            upper = [
                pooled["d1_ci_upper_pct"] - values[0],
                pooled["d7_ci_upper_pct"] - values[1],
            ]

            fig = go.Figure(
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color=["#4dfcff", "#b18cff"],
                    error_y={
                        "type": "data",
                        "symmetric": False,
                        "array": upper,
                        "arrayminus": lower,
                        "color": "#ffffff",
                        "thickness": 2,
                        "width": 5,
                    },
                    text=[f"{v:.2f}%" for v in values],
                    textposition="outside",
                    cliponaxis=False,
                )
            )
            fig.update_layout(
                title="Pooled retention with 95% Wilson intervals",
                xaxis_title="Retention checkpoint",
                yaxis_title="Retention (%)",
                **PLOT_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🗺️ INTELLIGENCE LOG")
        show_table(public_summary)

    st.divider()
    st.subheader("🎯 SELECT YOUR NEXT MISSION")

    a, b, c = st.columns(3)

    with a:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-icon">📊</div>
                <div class="mission-title">PLAYER OBSERVATORY</div>
                <div class="mission-copy">
                    Investigate cohorts, retention trends, and platform behavior.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-icon">⚔️</div>
                <div class="mission-title">EXPERIMENT ARENA</div>
                <div class="mission-copy">
                    Plan sample sizes and inspect experiment-readiness diagnostics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-icon">🛡️</div>
                <div class="mission-title">DATA INTEGRITY</div>
                <div class="mission-copy">
                    Audit source coverage, validation results, and assumptions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# PAGE 2 — PLAYER OBSERVATORY
# ============================================================

elif page == "Retention Explorer":
    section_header(
        "MISSION 02 // PLAYER OBSERVATORY",
        "Retention radar",
        "Filter the historical cohorts to investigate exact-day retention by platform.",
    )

    if public_daily is None or public_daily.empty:
        st.error("Daily retention data could not be loaded.")
        if daily_missing:
            st.write("Missing columns:", daily_missing)
    else:
        platforms = sorted(public_daily["platform"].dropna().unique().tolist())

        selected_platforms = st.multiselect(
            "🎮 Choose platforms",
            options=platforms,
            default=platforms,
        )

        min_date = public_daily["cohort_date"].min().date()
        max_date = public_daily["cohort_date"].max().date()

        date_range = st.date_input(
            "📅 Cohort launch window",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        filtered = public_daily[
            public_daily["platform"].isin(selected_platforms)
        ].copy()

        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start_date, end_date = date_range
            filtered = filtered[
                filtered["cohort_date"].dt.date.between(start_date, end_date)
            ]

        if filtered.empty:
            st.warning("No cohorts match the current mission parameters.")
        else:
            d1_rate = weighted_retention(filtered, "d1_retained_users")
            d7_rate = weighted_retention(filtered, "d7_retained_users")

            a, b, c, d = st.columns(4)

            with a:
                metric_card(
                    "COHORT DATES",
                    f"{filtered['cohort_date'].nunique():,}",
                    "Unique dates",
                )
            with b:
                metric_card(
                    "COHORT SEGMENTS",
                    f"{len(filtered):,}",
                    "Date-platform rows",
                )
            with c:
                metric_card(
                    "D1 CHECKPOINT",
                    f"{d1_rate:.2f}%" if pd.notna(d1_rate) else "N/A",
                    "Retained / cohort users",
                )
            with d:
                metric_card(
                    "D7 CHECKPOINT",
                    f"{d7_rate:.2f}%" if pd.notna(d7_rate) else "N/A",
                    "Retained / cohort users",
                )

            st.markdown("")
            checkpoint = st.segmented_control(
                "🎯 Select retention checkpoint",
                options=["D1", "D7"],
                default="D1",
            )

            if checkpoint == "D7":
                rate_col = "d7_retention_pct"
                retained_col = "d7_retained_users"
            else:
                rate_col = "d1_retention_pct"
                retained_col = "d1_retained_users"

            fig = px.line(
                filtered.sort_values("cohort_date"),
                x="cohort_date",
                y=rate_col,
                color="platform",
                markers=True,
                hover_data=["cohort_users", retained_col],
                color_discrete_sequence=["#4dfcff", "#b18cff", "#ff62ca"],
                labels={
                    "cohort_date": "Cohort launch date",
                    rate_col: "Retention (%)",
                    "platform": "Platform",
                    "cohort_users": "Cohort users",
                    retained_col: "Retained users",
                },
            )
            fig.update_traces(line={"width": 3}, marker={"size": 6})
            fig.update_layout(
                title=f"📡 {checkpoint} retention signal",
                yaxis_title="Retention (%)",
                **PLOT_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("🧩 COHORT HEATMAP")

            heatmap_data = filtered.pivot_table(
                index="platform",
                columns="cohort_date",
                values=rate_col,
                aggfunc="mean",
            ).sort_index(axis=1)

            fig = go.Figure(
                go.Heatmap(
                    z=heatmap_data.values,
                    x=[d.strftime("%Y-%m-%d") for d in heatmap_data.columns],
                    y=heatmap_data.index.tolist(),
                    zmin=0,
                    colorscale=[
                        [0.0, "#11182b"],
                        [0.35, "#3b347e"],
                        [0.7, "#536fd2"],
                        [1.0, "#4dfcff"],
                    ],
                    colorbar={"title": "Retention %"},
                    hovertemplate=(
                        "Platform: %{y}<br>Date: %{x}<br>"
                        "Retention: %{z:.2f}%<extra></extra>"
                    ),
                )
            )
            fig.update_layout(
                title=f"{checkpoint} retention by platform and cohort date",
                xaxis_title="Cohort date",
                yaxis_title="Platform",
                **PLOT_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 COHORT EVENT LOG")

            columns = [
                "cohort_date",
                "platform",
                "cohort_users",
                "d1_retained_users",
                "d1_retention_pct",
                "d7_retained_users",
                "d7_retention_pct",
            ]

            show_table(
                filtered[columns].sort_values(["cohort_date", "platform"])
            )

            st.download_button(
                "⬇ EXPORT FILTERED COHORTS",
                data=filtered[columns].to_csv(index=False).encode("utf-8"),
                file_name="filtered_flood_it_retention.csv",
                mime="text/csv",
            )

    st.markdown(
        """
        <div class="source-note">
            <strong>RETENTION PROTOCOL:</strong> D1 is a session on cohort day + 1.
            D7 is a session on cohort day + 7. These are exact-day metrics, not
            cumulative activity. Weighted rates use retained-user counts divided
            by the total cohort-user count in the selected rows.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# PAGE 3 — EXPERIMENT ARENA
# ============================================================

elif page == "Experiment Lab":
    section_header(
        "MISSION 03 // EXPERIMENT ARENA",
        "Experiment control room",
        "Plan a hypothetical A/B experiment and inspect the existing synthetic readiness run.",
    )

    st.subheader("⚙️ MISSION CONFIGURATION")
    st.caption(
        "The sample-size estimate uses a two-sided normal approximation for two "
        "independent proportions with equal group allocation."
    )

    left, right = st.columns(2)

    with left:
        baseline_pct = st.number_input(
            "Baseline conversion / retention (%)",
            min_value=1.0,
            max_value=98.0,
            value=30.0,
            step=1.0,
        )
        target_pct = st.number_input(
            "Target conversion / retention (%)",
            min_value=2.0,
            max_value=99.0,
            value=35.0,
            step=1.0,
        )

    with right:
        alpha = st.selectbox(
            "Significance threshold",
            [0.01, 0.05, 0.10],
            index=1,
            format_func=lambda x: f"{x:.0%}",
        )
        power = st.selectbox(
            "Desired statistical power",
            [0.80, 0.85, 0.90, 0.95],
            index=0,
            format_func=lambda x: f"{x:.0%}",
        )

    baseline = baseline_pct / 100
    target = target_pct / 100

    if baseline == target:
        st.warning("The baseline and target rates must differ.")
    else:
        z_alpha = norm.ppf(1 - alpha / 2)
        z_power = norm.ppf(power)
        average_rate = (baseline + target) / 2
        effect = abs(target - baseline)

        n = (
            z_alpha * math.sqrt(2 * average_rate * (1 - average_rate))
            + z_power
            * math.sqrt(
                baseline * (1 - baseline)
                + target * (1 - target)
            )
        ) ** 2 / effect**2

        per_arm = math.ceil(n)
        total = per_arm * 2

        a, b, c = st.columns(3)

        with a:
            metric_card(
                "CONTROL SLOTS",
                f"{per_arm:,}",
                "Approximate players per arm",
            )
        with b:
            metric_card(
                "TOTAL DEPLOYMENT",
                f"{total:,}",
                "Equal-sized groups",
            )
        with c:
            metric_card(
                "TARGET LIFT",
                f"{abs(target_pct - baseline_pct):.1f} pp",
                "Absolute percentage-point difference",
            )

        st.markdown(
            """
            <div class="mission-banner">
                <strong>MISSION NOTE:</strong> This is a planning estimate,
                not evidence of an achieved lift. It does not account for every
                practical issue such as repeated testing, clustering, or attrition.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("🧪 SYNTHETIC EXPERIMENT RUN")

    st.markdown(
        """
        <div class="source-note">
            <strong>SYNTHETIC SIMULATION ONLY.</strong> Existing assignments
            were applied to pre-existing synthetic outcomes. No treatment effect
            was simulated. This comparison is not causal evidence about real players.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if srm_result:
        control = srm_result.get("control_count")
        treatment = srm_result.get("treatment_count")
        p_value = srm_result.get("p_value")
        flagged = srm_result.get("srm_flag")

        a, b, c = st.columns(3)

        with a:
            metric_card(
                "CONTROL TEAM",
                f"{control:,}" if control is not None else "N/A",
                "Synthetic assignments",
            )
        with b:
            metric_card(
                "TREATMENT TEAM",
                f"{treatment:,}" if treatment is not None else "N/A",
                "Synthetic assignments",
            )
        with c:
            metric_card(
                "SRM DIAGNOSTIC",
                "FLAGGED" if flagged else "CLEAR",
                f"p = {p_value:.4f}" if p_value is not None else "See details",
            )

        if flagged:
            st.warning(
                "The sample-ratio mismatch check was flagged. Investigate "
                "assignment, eligibility, and event logging before interpreting results."
            )
        else:
            st.success(
                "The configured SRM check did not flag allocation imbalance. "
                "This does not prove that all experiment assumptions are satisfied."
            )

        with st.expander("View allocation diagnostics"):
            st.json(srm_result)
    else:
        st.info("SRM output is unavailable. Run the existing readiness script.")

    if synthetic_metrics is not None and not synthetic_metrics.empty:
        st.subheader("📈 CONTROL VS TREATMENT")

        required = {
            "metric",
            "control_rate_pct",
            "treatment_rate_pct",
        }

        if required.issubset(synthetic_metrics.columns):
            plot_df = synthetic_metrics.copy()
            plot_df["label"] = (
                plot_df["metric"].astype(str).str.replace(
                    "_retained", "", regex=False
                ).str.upper()
            )

            plot_long = plot_df.melt(
                id_vars=["label"],
                value_vars=["control_rate_pct", "treatment_rate_pct"],
                var_name="group",
                value_name="rate",
            )
            plot_long["group"] = plot_long["group"].map(
                {
                    "control_rate_pct": "Control",
                    "treatment_rate_pct": "Treatment",
                }
            )

            fig = px.bar(
                plot_long,
                x="label",
                y="rate",
                color="group",
                barmode="group",
                text="rate",
                color_discrete_map={
                    "Control": "#b18cff",
                    "Treatment": "#4dfcff",
                },
                labels={
                    "label": "Metric",
                    "rate": "Retention (%)",
                    "group": "Assignment",
                },
            )
            fig.update_traces(
                texttemplate="%{y:.2f}%",
                textposition="outside",
                cliponaxis=False,
            )
            fig.update_layout(
                title="Synthetic outcome comparison",
                yaxis_title="Retention (%)",
                **PLOT_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

            display_columns = [
                col for col in [
                    "metric",
                    "control_n",
                    "treatment_n",
                    "control_rate_pct",
                    "treatment_rate_pct",
                    "absolute_lift_pp",
                    "relative_lift_pct",
                    "difference_ci_low_pp",
                    "difference_ci_high_pp",
                    "p_value",
                ]
                if col in synthetic_metrics.columns
            ]

            show_table(synthetic_metrics[display_columns])
        else:
            st.info(
                "The synthetic metric schema differs from the expected comparison "
                "columns. Displaying the available records instead."
            )
            show_table(synthetic_metrics)

    else:
        st.info("Synthetic experiment metrics are unavailable.")

    if synthetic_report:
        with st.expander("Read the full experiment readiness report"):
            st.markdown(synthetic_report)


# ============================================================
# PAGE 4 — DATA INTEGRITY
# ============================================================

elif page == "Data Quality":
    section_header(
        "MISSION 04 // DATA INTEGRITY",
        "Data integrity shield",
        "Audit the exports, source coverage, and analytical safeguards.",
    )

    passed = validation_status(quality_text)

    table_count = None
    if date_coverage is not None and "daily_table_count" in date_coverage.columns:
        values = pd.to_numeric(
            date_coverage["daily_table_count"], errors="coerce"
        ).dropna()
        if not values.empty:
            table_count = int(values.iloc[0])

    missing_ids = None
    if (
        event_quality is not None
        and "events_missing_user_id" in event_quality.columns
    ):
        missing_ids = int(
            pd.to_numeric(
                event_quality["events_missing_user_id"], errors="coerce"
            ).fillna(0).sum()
        )

    a, b, c = st.columns(3)

    with a:
        metric_card(
            "VALIDATION SHIELD",
            "PASS" if passed else "CHECK",
            "5 files / 0 errors / 0 warnings"
            if passed else "Inspect the validation report",
        )
    with b:
        metric_card(
            "SOURCE TABLES",
            f"{table_count:,}" if table_count is not None else "N/A",
            "Historical daily tables",
        )
    with c:
        metric_card(
            "MISSING USER IDs",
            f"{missing_ids:,}" if missing_ids is not None else "N/A",
            "Selected event-quality export",
        )

    if passed:
        st.markdown(
            '<div class="status-pass">✓ EXPORT VALIDATION PASSED — configured checks returned zero errors and zero warnings.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-warning">Review the export validation report before relying on the data.</div>',
            unsafe_allow_html=True,
        )

    if quality_text:
        with st.expander("📜 Public export validation log", expanded=True):
            st.code(quality_text, language="text")
    else:
        st.warning(
            "Validation report not found. Run "
            "src/data/validate_flood_it_exports.py."
        )

    st.subheader("🧬 DATA SOURCE REGISTRY")

    provenance = pd.DataFrame(
        [
            {
                "Dataset": "Public Flood-It! sample",
                "Purpose": "Validate event processing and retention methods",
                "Limitation": "Not an idle game; not Kolibri Games data",
            },
            {
                "Dataset": "Synthetic idle-game fixture",
                "Purpose": "Test pipeline and experiment-quality logic",
                "Limitation": "Not real player behavior or real treatment effects",
            },
        ]
    )
    show_table(provenance)

    st.subheader("🛡️ ANALYTICAL SAFEGUARDS")

    safeguards = [
        ("01", "Cohort entry", "Earliest observed first_open date per pseudonymous user."),
        ("02", "Retention event", "session_start on the exact target day."),
        ("03", "Follow-up", "Exclude cohorts without the required observation window."),
        ("04", "Uncertainty", "Wilson confidence intervals for binomial retention."),
        ("05", "Experiment quality", "SRM checks do not prove all experiment assumptions."),
        ("06", "Instrumentation", "No observed session does not necessarily mean churn."),
    ]

    for number, title, description in safeguards:
        st.markdown(
            f"""
            <div class="mission-banner">
                <strong style="color:#4dfcff;font-family:Orbitron,sans-serif;">
                    {number} // {title.upper()}
                </strong><br>
                {description}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if findings_text:
        with st.expander("📊 Read the complete retention findings"):
            st.markdown(findings_text)

    st.subheader("📦 LOCAL ARTIFACT INVENTORY")

    artifacts = [
        DAILY_FILE,
        SUMMARY_FILE,
        EVENT_QUALITY_FILE,
        DATE_COVERAGE_FILE,
        QUALITY_FILE,
        FINDINGS_FILE,
        SYNTHETIC_METRICS_FILE,
        SYNTHETIC_SRM_FILE,
        SYNTHETIC_COHORT_FILE,
    ]

    inventory = pd.DataFrame(
        [
            {
                "Artifact": str(path.relative_to(ROOT)),
                "Status": "AVAILABLE" if path.exists() else "NOT FOUND",
            }
            for path in artifacts
        ]
    )
    show_table(inventory)


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown(
    """
    <div class="footer">
        IDLE LOOP OBSERVATORY // PLAYER INTELLIGENCE DIVISION<br>
        PUBLIC FLOOD-IT! DATA AND SYNTHETIC IDLE-GAME DATA REMAIN SEPARATE.<br>
        ANALYTICS PROTOTYPE // INTERPRET RESULTS WITH THEIR DOCUMENTED LIMITATIONS.
    </div>
    """,
    unsafe_allow_html=True,
)
