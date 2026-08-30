"""Shared Executive Fintech presentation helpers for the Streamlit app."""
from __future__ import annotations

from html import escape

import plotly.graph_objects as go
import streamlit as st


INK = "#F8FAFC"
MUTED = "#94A3B8"
GREEN = "#34D399"
CYAN = "#38BDF8"
AMBER = "#FBBF24"
RED = "#FB7185"
PURPLE = "#A78BFA"
CHART_COLORS = [GREEN, CYAN, PURPLE, AMBER, RED, "#2DD4BF", "#60A5FA"]


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #060D17;
            --surface: rgba(13, 27, 44, 0.88);
            --surface-2: rgba(18, 35, 55, 0.82);
            --border: rgba(148, 163, 184, 0.14);
            --text: #F8FAFC;
            --muted: #94A3B8;
            --green: #34D399;
            --cyan: #38BDF8;
            --red: #FB7185;
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 88% 4%, rgba(16,185,129,.10), transparent 23rem),
                radial-gradient(circle at 12% 18%, rgba(56,189,248,.08), transparent 25rem),
                var(--bg);
            color: var(--text);
        }

        [data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }
        .block-container {
            max-width: 1440px;
            padding-top: 1.6rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #08131F 0%, #0B1725 100%);
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
        [data-testid="stSidebar"] hr { border-color: var(--border); }

        .brand {
            display: flex;
            align-items: center;
            gap: .75rem;
            margin: .15rem 0 1.25rem;
        }
        .brand-icon {
            display: grid;
            place-items: center;
            width: 2.65rem;
            height: 2.65rem;
            border-radius: .8rem;
            background: linear-gradient(135deg, #34D399, #0EA5E9);
            box-shadow: 0 10px 35px rgba(52,211,153,.22);
            color: #03120C;
            font-size: 1.25rem;
            font-weight: 900;
        }
        .brand-name { color: var(--text); font-size: 1.05rem; font-weight: 800; letter-spacing: -.02em; }
        .brand-sub { color: var(--muted); font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }

        .hero-shell {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 2rem;
            align-items: end;
            padding: 2.2rem 2.35rem;
            margin-bottom: 1.25rem;
            border: 1px solid rgba(52,211,153,.18);
            border-radius: 1.35rem;
            background:
                linear-gradient(120deg, rgba(15,34,52,.96), rgba(8,23,37,.96)),
                var(--surface);
            box-shadow: 0 24px 80px rgba(0,0,0,.28);
        }
        .hero-shell::after {
            content: "";
            position: absolute;
            width: 22rem;
            height: 22rem;
            right: -10rem;
            top: -13rem;
            border-radius: 50%;
            background: rgba(52,211,153,.12);
            filter: blur(2px);
        }
        .eyebrow {
            color: var(--green);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
            margin-bottom: .55rem;
        }
        .hero-title {
            color: var(--text);
            font-size: clamp(2.05rem, 4vw, 3.35rem);
            line-height: 1.02;
            letter-spacing: -.055em;
            font-weight: 850;
            margin: 0;
        }
        .hero-copy {
            color: #B8C5D3;
            max-width: 48rem;
            font-size: .98rem;
            line-height: 1.65;
            margin: .85rem 0 0;
        }
        .hero-meta { display: flex; gap: .65rem; flex-wrap: wrap; position: relative; z-index: 2; }
        .meta-pill {
            border: 1px solid var(--border);
            border-radius: 999px;
            background: rgba(255,255,255,.035);
            color: #C8D3DE;
            padding: .46rem .72rem;
            font-size: .75rem;
            white-space: nowrap;
        }
        .meta-pill.live { border-color: rgba(52,211,153,.3); color: #8FF0C7; }
        .live-dot {
            display: inline-block;
            width: .42rem;
            height: .42rem;
            margin-right: .35rem;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 0 4px rgba(52,211,153,.1);
        }

        .section-head { margin: 1.2rem 0 .9rem; }
        .section-kicker {
            color: var(--green);
            font-size: .68rem;
            font-weight: 800;
            letter-spacing: .13em;
            text-transform: uppercase;
            margin-bottom: .25rem;
        }
        .section-title { color: var(--text); font-size: 1.35rem; font-weight: 760; letter-spacing: -.025em; }
        .section-copy { color: var(--muted); font-size: .86rem; margin-top: .22rem; }

        div[data-testid="stMetric"] {
            min-height: 8rem;
            padding: 1.15rem 1.2rem;
            border: 1px solid var(--border);
            border-radius: 1rem;
            background: linear-gradient(145deg, rgba(16,32,50,.9), rgba(10,24,39,.92));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 10px 30px rgba(0,0,0,.12);
        }
        div[data-testid="stMetricLabel"] { color: var(--muted); font-size: .76rem; }
        div[data-testid="stMetricValue"] { color: var(--text); letter-spacing: -.04em; }
        div[data-testid="stMetricDelta"] { font-size: .72rem; }

        .stTabs [data-baseweb="tab-list"] {
            gap: .3rem;
            padding: .35rem;
            margin: 1.2rem 0 1.35rem;
            border: 1px solid var(--border);
            border-radius: .95rem;
            background: rgba(10,24,39,.82);
        }
        .stTabs [data-baseweb="tab"] {
            height: 2.55rem;
            border-radius: .7rem;
            padding: 0 .9rem;
            color: var(--muted);
            font-size: .81rem;
            font-weight: 650;
        }
        .stTabs [aria-selected="true"] {
            color: #E9FFF7 !important;
            background: rgba(52,211,153,.12) !important;
        }
        .stTabs [data-baseweb="tab-highlight"] { display: none; }

        div[data-testid="stForm"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border);
            border-radius: 1rem;
            background: rgba(12,27,44,.54);
        }
        div[data-testid="stExpander"] {
            border-color: var(--border);
            border-radius: .85rem;
            background: rgba(255,255,255,.018);
        }
        .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
            border: 1px solid rgba(52,211,153,.25);
            border-radius: .72rem;
            background: linear-gradient(135deg, #1BC98E, #0EA5A0);
            color: #02140E;
            font-weight: 750;
            box-shadow: 0 8px 24px rgba(16,185,129,.13);
            transition: transform .16s ease, box-shadow .16s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
            color: #02140E;
            border-color: #6EE7B7;
            transform: translateY(-1px);
            box-shadow: 0 12px 28px rgba(16,185,129,.22);
        }

        .safe-card {
            min-height: 15rem;
            padding: 1.65rem;
            border: 1px solid rgba(52,211,153,.22);
            border-radius: 1.15rem;
            background:
                radial-gradient(circle at 85% 20%, rgba(52,211,153,.12), transparent 40%),
                linear-gradient(145deg, rgba(13,37,48,.95), rgba(10,25,40,.96));
            box-shadow: 0 20px 50px rgba(0,0,0,.18);
        }
        .safe-label { color: #8FA5B8; font-size: .75rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 750; }
        .safe-value { color: #E9FFF7; font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 850; letter-spacing: -.065em; margin: .3rem 0 .1rem; }
        .safe-sub { color: #AFC0CF; font-size: .9rem; }
        .status-chip {
            display: inline-block;
            margin-top: 1.35rem;
            padding: .42rem .7rem;
            border-radius: 999px;
            font-size: .73rem;
            font-weight: 750;
            border: 1px solid rgba(52,211,153,.28);
            background: rgba(52,211,153,.1);
            color: #8FF0C7;
        }
        .status-chip.warn { border-color: rgba(251,191,36,.3); background: rgba(251,191,36,.1); color: #FDE68A; }
        .status-chip.risk { border-color: rgba(251,113,133,.3); background: rgba(251,113,133,.1); color: #FDA4AF; }

        .insight-card {
            min-height: 7.25rem;
            padding: 1.05rem 1.1rem;
            border: 1px solid var(--border);
            border-radius: .95rem;
            background: linear-gradient(145deg, rgba(16,32,50,.84), rgba(9,22,36,.9));
            color: #C9D5E0;
            font-size: .86rem;
            line-height: 1.55;
        }
        .insight-index { color: var(--green); font-size: .68rem; font-weight: 850; letter-spacing: .1em; margin-bottom: .45rem; }

        .empty-card {
            padding: 3.5rem 2rem;
            text-align: center;
            border: 1px dashed rgba(148,163,184,.22);
            border-radius: 1.2rem;
            background: rgba(13,27,44,.5);
        }
        .empty-title { color: var(--text); font-size: 1.35rem; font-weight: 780; }
        .empty-copy { color: var(--muted); margin-top: .4rem; }

        [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: .9rem; overflow: hidden; }
        [data-testid="stAlert"] { border-radius: .85rem; border-color: var(--border); }
        [data-testid="stProgress"] > div > div { background: linear-gradient(90deg, #34D399, #38BDF8); }

        @media (max-width: 900px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .hero-shell { grid-template-columns: 1fr; padding: 1.55rem; }
            .hero-meta { margin-top: .4rem; }
            .stTabs [data-baseweb="tab"] { padding: 0 .62rem; font-size: .74rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-icon">₹</div>
          <div>
            <div class="brand-name">FinSight</div>
            <div class="brand-sub">Finance Intelligence</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(start_date: str, end_date: str, transaction_count: int) -> None:
    st.markdown(
        f"""
        <div class="hero-shell">
          <div>
            <div class="eyebrow">Personal finance intelligence</div>
            <h1 class="hero-title">Money, understood.</h1>
            <p class="hero-copy">A decision-focused financial command center that turns transaction data into forecasts, risk signals, and an actionable monthly plan.</p>
          </div>
          <div class="hero-meta">
            <span class="meta-pill live"><span class="live-dot"></span>Analytics live</span>
            <span class="meta-pill">{transaction_count:,} transactions</span>
            <span class="meta-pill">{escape(start_date)} — {escape(end_date)}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(kicker: str, title: str, description: str = "") -> None:
    copy = f'<div class="section-copy">{escape(description)}</div>' if description else ""
    st.markdown(
        f"""
        <div class="section-head">
          <div class="section-kicker">{escape(kicker)}</div>
          <div class="section-title">{escape(title)}</div>
          {copy}
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(index: int, text: str) -> None:
    clean = escape(text.replace("**", ""))
    st.markdown(
        f'<div class="insight-card"><div class="insight-index">SIGNAL {index:02d}</div>{clean}</div>',
        unsafe_allow_html=True,
    )


def safe_spend_card(amount: float, daily: float, days: int, status: str, message: str) -> None:
    chip_class = "" if status == "On track" else "warn" if status in {"At risk", "Goal too high"} else "risk"
    st.markdown(
        f"""
        <div class="safe-card">
          <div class="safe-label">Available after goals &amp; commitments</div>
          <div class="safe-value">₹{amount:,.0f}</div>
          <div class="safe-sub">₹{daily:,.0f} per day across {days} remaining day{'s' if days != 1 else ''}</div>
          <span class="status-chip {chip_class}">{escape(status)} · {escape(message)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig: go.Figure, height: int = 360, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": MUTED, "size": 12},
        margin={"l": 18, "r": 18, "t": 30, "b": 18},
        colorway=CHART_COLORS,
        hoverlabel={"bgcolor": "#102338", "font_color": INK, "bordercolor": "#233C55"},
        showlegend=legend,
        legend={
            "orientation": "h", "yanchor": "bottom", "y": 1.02,
            "xanchor": "right", "x": 1, "title_text": "",
        },
    )
    fig.update_xaxes(showgrid=False, linecolor="rgba(148,163,184,.12)", tickfont_color=MUTED)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.10)", zeroline=False, tickfont_color=MUTED)
    return fig
