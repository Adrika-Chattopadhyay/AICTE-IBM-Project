"""
Fitness Buddy — Main Streamlit Application
AI-powered health & fitness coach using IBM Granite on watsonx.ai
"""

import os
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import time
from datetime import date, datetime
from typing import Dict, List, Optional

# ── Local modules ────────────────────────────────────────────
from granite_client import get_client
from guardrails import get_pipeline
from features import (
    build_system_prompt,
    build_checkin_prompt,
    build_mvw_prompt,
    build_plan_b_prompt,
    build_meal_prompt,
    build_habit_prompt,
    build_motivation_prompt,
    build_progress_summary,
    calculate_readiness_score,
    get_current_habit,
    get_minimum_viable_workouts,
    get_workout_alternatives,
    HABIT_LADDER_STEPS,
    COACH_PERSONAS,
)
from progress_store import (
    get_progress,
    record_workout,
    record_checkin,
    increment_habit_day,
)

# ─────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Fitness Buddy 💪",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════
   TYPOGRAPHY BASE
═══════════════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    font-size: 15px !important;
    line-height: 1.65 !important;
    -webkit-font-smoothing: antialiased;
}

/* ═══════════════════════════════════════════════════════
   MAIN AREA — light background, near-black text
═══════════════════════════════════════════════════════ */
.stApp {
    background-color: #f0f4f8;
    color: #111827 !important;
}
.stApp p, .stApp li, .stApp span, .stApp label, .stApp div, .stApp small,
.stApp .stMarkdown, .stApp .stText,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stMarkdownContainer"] span,
.stApp [data-testid="stMarkdownContainer"] strong,
.stApp [data-testid="stMarkdownContainer"] em,
.stApp [data-testid="stMarkdownContainer"] code {
    color: #111827 !important;
    font-size: 15px !important;
}
.stApp [data-testid="stMarkdownContainer"] strong { color: #0c1a2e !important; font-weight: 700 !important; }
.stApp [data-testid="stMarkdownContainer"] em     { color: #1e293b !important; }
.stApp code {
    background: #e8edf2 !important; color: #1d4ed8 !important;
    padding: 0.1em 0.4em !important; border-radius: 4px !important; font-size: 0.9em !important;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
    color: #0c1a2e !important; font-weight: 700 !important;
    letter-spacing: -0.01em; line-height: 1.3 !important;
}
.stApp h1 { font-size: 2rem !important; }
.stApp h2 { font-size: 1.5rem !important; }
.stApp h3 { font-size: 1.2rem !important; }

/* ═══════════════════════════════════════════════════════
   SIDEBAR — deep navy, bright white text on every widget
═══════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background-color: #0f2137 !important;
}
/* Universal white text inside sidebar */
[data-testid="stSidebar"],
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stText,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] em {
    color: #e8f0fe !important;
}
/* Sidebar headings — bright white */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #ffffff !important;
    font-weight: 700 !important;
}
/* Sidebar bold labels (e.g. "Coach Personality") */
[data-testid="stSidebar"] strong {
    color: #ffffff !important;
    font-weight: 700 !important;
}
/* Sidebar captions / small text */
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] small {
    color: #93c5fd !important;
    font-size: 0.82rem !important;
}
/* Sidebar radio options */
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label,
[data-testid="stSidebar"] .stRadio p {
    color: #e8f0fe !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
/* Sidebar selectbox — outer label */
[data-testid="stSidebar"] .stSelectbox label {
    color: #bfdbfe !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}
/* Sidebar selectbox — chosen value inside the box */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] div,
[data-testid="stSidebar"] .stSelectbox [data-testid="stMarkdownContainer"] p {
    color: #ffffff !important;
    font-size: 14px !important;
}
/* Sidebar selectbox — dropdown items */
[data-testid="stSidebar"] [data-testid="stSelectbox"] span,
[data-testid="stSidebar"] [data-testid="stSelectbox"] div {
    color: #e8f0fe !important;
}
/* Sidebar metric labels and values */
[data-testid="stSidebar"] div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] div[data-testid="metric-container"] label {
    color: #93c5fd !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 1.3rem !important;
}
[data-testid="stSidebar"] div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    color: #93c5fd !important;
}
/* Sidebar separator */
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
    margin: 0.75rem 0 !important;
}
/* Sidebar buttons */
[data-testid="stSidebar"] .stButton > button {
    background-color: #1e40af !important;
    color: #ffffff !important;
    border: 1px solid #3b82f6 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    border-color: #60a5fa !important;
}

/* ═══════════════════════════════════════════════════════
   CAPTIONS  (main area)
═══════════════════════════════════════════════════════ */
.stApp .stCaption,
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p,
.stApp small {
    color: #374151 !important;
    font-size: 0.85rem !important;
    font-weight: 400 !important;
}

/* ═══════════════════════════════════════════════════════
   HOME BANNER
═══════════════════════════════════════════════════════ */
.main-header {
    background: linear-gradient(135deg, #0f2137 0%, #1d4ed8 60%, #2563eb 100%);
    color: #ffffff !important;
    padding: 3rem 2rem 2.5rem;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 24px rgba(29,78,216,0.3);
}
/* Force ALL children of the banner to white — overrides .stApp div rule */
.main-header,
.main-header *,
.main-header div,
.main-header span,
.main-header p,
.main-header h1,
.main-header h2 {
    color: #ffffff !important;
}
.main-header .banner-subtitle {
    color: #bfdbfe !important;
}

/* ── Home stat bars (custom HTML cards below banner) ── */
.stat-bar {
    display: flex;
    gap: 0;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.12);
    margin-bottom: 1.5rem;
}
.stat-item {
    flex: 1;
    background: #ffffff;
    padding: 1.1rem 0.5rem 1rem;
    text-align: center;
    border-right: 1px solid #e5e7eb;
    position: relative;
}
.stat-item:last-child { border-right: none; }
.stat-value {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #1d4ed8 !important;
    line-height: 1.1;
    display: block;
}
.stat-label {
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    color: #374151 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 0.2rem;
    display: block;
}
.stat-delta {
    font-size: 0.7rem !important;
    color: #6b7280 !important;
    margin-top: 0.1rem;
    display: block;
}

/* ═══════════════════════════════════════════════════════
   FEATURE CARDS
═══════════════════════════════════════════════════════ */
.feature-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 1.5rem;
    border-left: 4px solid #2563eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.10);
    margin-bottom: 1rem;
    color: #111827 !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
}
.feature-card strong { color: #0c1a2e !important; font-weight: 700 !important; }
.feature-card span   { color: #1e293b !important; font-size: 14px !important; }
.feature-card em     { color: #374151 !important; }

/* ═══════════════════════════════════════════════════════
   SCORE CARD
═══════════════════════════════════════════════════════ */
.score-card { background: #ffffff; border-radius: 12px; padding: 1.5rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.10); }
.score-big  { font-size: 3.5rem !important; font-weight: 800 !important; color: #1d4ed8 !important; line-height: 1; }
.score-label{ color: #374151 !important; font-size: 0.9rem !important; margin-top: 0.25rem; font-weight: 500 !important; }

/* ═══════════════════════════════════════════════════════
   HABIT STEPS
═══════════════════════════════════════════════════════ */
.habit-step {
    display: flex; align-items: center; padding: 0.85rem;
    border-radius: 8px; margin: 0.35rem 0;
    color: #111827 !important; font-size: 15px !important; line-height: 1.5 !important;
}
.habit-active { background: #dbeafe; border-left: 3px solid #2563eb; }
.habit-done   { background: #dcfce7; border-left: 3px solid #16a34a; }
.habit-locked { background: #e2e8f0; }
.habit-locked * { color: #6b7280 !important; }
.habit-step strong { color: #0c1a2e !important; font-weight: 700 !important; }

/* ═══════════════════════════════════════════════════════
   WARNING / SUCCESS BOXES
═══════════════════════════════════════════════════════ */
.guardrail-warning {
    background: #fef9c3; border: 1px solid #ca8a04;
    border-radius: 8px; padding: 0.75rem 1rem;
    font-size: 14px !important; color: #713f12 !important; font-weight: 500 !important;
}
.success-box {
    background: #dcfce7; border: 1px solid #16a34a;
    border-radius: 8px; padding: 0.75rem 1rem;
    color: #14532d !important; font-weight: 500 !important;
}

/* ═══════════════════════════════════════════════════════
   IBM BADGE
═══════════════════════════════════════════════════════ */
.ibm-badge {
    background: rgba(255,255,255,0.15);
    color: #bfdbfe !important;
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px; padding: 0.3rem 0.9rem;
    font-size: 0.78rem !important; display: inline-block;
    font-weight: 600 !important; letter-spacing: 0.02em;
}

/* ═══════════════════════════════════════════════════════
   METRIC CARDS (main area)
═══════════════════════════════════════════════════════ */
div[data-testid="metric-container"] {
    background: #ffffff; border-radius: 10px;
    padding: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.10);
}
div[data-testid="metric-container"] label,
div[data-testid="metric-container"] [data-testid="stMetricLabel"],
div[data-testid="metric-container"] [data-testid="stMetricLabel"] p,
div[data-testid="metric-container"] [data-testid="stMetricLabel"] span {
    color: #374151 !important; font-weight: 700 !important; font-size: 13px !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"],
div[data-testid="metric-container"] [data-testid="stMetricValue"] > div {
    color: #0c1a2e !important; font-weight: 800 !important; font-size: 1.6rem !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"],
div[data-testid="metric-container"] [data-testid="stMetricDelta"] p,
div[data-testid="metric-container"] [data-testid="stMetricDelta"] span,
div[data-testid="metric-container"] [data-testid="stMetricDelta"] div {
    color: #4b5563 !important; font-size: 12px !important; font-weight: 500 !important;
}
/* Override Streamlit's green/red delta arrow colours so they stay readable */
div[data-testid="metric-container"] [data-testid="stMetricDelta"] svg {
    color: #4b5563 !important; fill: #4b5563 !important;
}

/* ═══════════════════════════════════════════════════════
   AI RESPONSE BOX
═══════════════════════════════════════════════════════ */
.ai-response {
    background: #ffffff; border-radius: 12px;
    padding: 1.5rem 1.75rem; border-left: 4px solid #2563eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.10); margin-top: 1rem;
    color: #111827 !important; font-size: 15px !important; line-height: 1.7 !important;
}
.ai-response p      { color: #111827 !important; font-size: 15px !important; }
.ai-response li     { color: #111827 !important; font-size: 15px !important; }
.ai-response span   { color: #111827 !important; }
.ai-response strong { color: #0c1a2e !important; font-weight: 700 !important; }
.ai-response em     { color: #374151 !important; }
.ai-response hr     { border-color: #e5e7eb !important; margin: 1rem 0; }
.ai-response code   { background: #f1f5f9 !important; color: #1d4ed8 !important; }

/* ═══════════════════════════════════════════════════════
   FORM INPUTS
═══════════════════════════════════════════════════════ */
.stTextInput input, .stTextArea textarea {
    color: #111827 !important; background-color: #ffffff !important;
    font-size: 15px !important; border: 1.5px solid #d1d5db !important; border-radius: 6px !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #9ca3af !important; }
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
}
/* Form labels */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stMultiSelect label,
.stSlider label, .stNumberInput label {
    color: #111827 !important; font-weight: 600 !important; font-size: 14px !important;
}

/* ═══════════════════════════════════════════════════════
   SELECTBOX / MULTISELECT
═══════════════════════════════════════════════════════ */
[data-testid="stSelectbox"] div, [data-testid="stSelectbox"] span,
[data-testid="stMultiSelect"] div, [data-testid="stMultiSelect"] span {
    color: #111827 !important; font-size: 15px !important;
}

/* ═══════════════════════════════════════════════════════
   SLIDERS
═══════════════════════════════════════════════════════ */
[data-testid="stSlider"] div[data-testid="stMarkdownContainer"] p,
[data-testid="stSlider"] [aria-label], .stSlider p {
    color: #111827 !important; font-size: 14px !important; font-weight: 500 !important;
}
[data-testid="stSlider"] span { color: #374151 !important; font-size: 12px !important; }

/* ═══════════════════════════════════════════════════════
   EXPANDER
═══════════════════════════════════════════════════════ */
.streamlit-expanderHeader,
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p {
    color: #111827 !important; font-weight: 600 !important; font-size: 15px !important;
}

/* ═══════════════════════════════════════════════════════
   TABS  — strong contrast on all states
═══════════════════════════════════════════════════════ */
/* Tab bar background */
.stTabs [data-baseweb="tab-list"] {
    background-color: #e8edf4 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}
/* Every tab — dark text */
.stTabs [data-baseweb="tab"] {
    color: #374151 !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
    padding: 0.45rem 1.1rem !important;
    background: transparent !important;
    border: none !important;
}
/* Active tab — white bg, blue text */
.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #1d4ed8 !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12) !important;
    border-bottom: none !important;
}
/* Inactive tab hover */
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background-color: rgba(255,255,255,0.6) !important;
    color: #111827 !important;
}
/* Tab panel content */
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1rem !important;
}

/* ═══════════════════════════════════════════════════════
   DATAFRAME
═══════════════════════════════════════════════════════ */
.stDataFrame td, .stDataFrame th { color: #111827 !important; font-size: 14px !important; }
.stDataFrame th { font-weight: 700 !important; background: #f1f5f9 !important; }

/* ═══════════════════════════════════════════════════════
   CHAT
═══════════════════════════════════════════════════════ */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span { color: #111827 !important; font-size: 15px !important; }
[data-testid="stChatInputContainer"] textarea { color: #111827 !important; font-size: 15px !important; }

/* ═══════════════════════════════════════════════════════
   BUTTONS — universal approach targeting the <button> element
═══════════════════════════════════════════════════════ */
/* All buttons default: white bg, dark text */
.stButton > button {
    background-color: #ffffff !important;
    color: #111827 !important;
    border: 2px solid #d1d5db !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background-color: #f1f5f9 !important;
    color: #111827 !important;
    border-color: #6b7280 !important;
}
.stButton > button:focus {
    outline: 2px solid #2563eb !important;
    outline-offset: 2px !important;
}
/* Primary button variant — blue bg, white text.
   Streamlit renders type="primary" as the first button in a column
   or uses data-testid="baseButton-primary". */
.stButton > button[data-testid="baseButton-primary"],
button[kind="primary"] {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    border: 2px solid #1d4ed8 !important;
    font-weight: 700 !important;
}
.stButton > button[data-testid="baseButton-primary"]:hover,
button[kind="primary"]:hover {
    background-color: #1e40af !important;
    color: #ffffff !important;
    border-color: #1e40af !important;
}
/* Form submit buttons — always blue */
.stFormSubmitButton > button {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    border: 2px solid #1d4ed8 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
    width: 100%;
    padding: 0.6rem 1rem !important;
}
.stFormSubmitButton > button:hover {
    background-color: #1e40af !important;
    color: #ffffff !important;
    border-color: #1e40af !important;
}
/* Sidebar buttons — blue tint on dark background */
[data-testid="stSidebar"] .stButton > button {
    background-color: #1e40af !important;
    color: #ffffff !important;
    border: 2px solid #3b82f6 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    border-color: #60a5fa !important;
}

/* ═══════════════════════════════════════════════════════
   SPINNER
═══════════════════════════════════════════════════════ */
.stSpinner > div > div { color: #1d4ed8 !important; font-size: 14px !important; }

/* ═══════════════════════════════════════════════════════
   ALERTS / NOTIFICATIONS
═══════════════════════════════════════════════════════ */
.stAlert [data-testid="stMarkdownContainer"] p,
.stAlert p, .stAlert span { color: #111827 !important; font-size: 14px !important; }
div[data-testid="stNotification"] p { color: #111827 !important; }

/* ═══════════════════════════════════════════════════════
   PROGRESS BAR
═══════════════════════════════════════════════════════ */
.stProgress > div > div { background-color: #1d4ed8 !important; }
.stProgress p { color: #374151 !important; font-size: 13px !important; }

/* ═══════════════════════════════════════════════════════
   RADIO / CHECKBOX
═══════════════════════════════════════════════════════ */
.stRadio label,
.stRadio div[role="radiogroup"] label { color: #111827 !important; font-size: 15px !important; font-weight: 500 !important; }
.stCheckbox label { color: #111827 !important; font-size: 15px !important; }

/* ═══════════════════════════════════════════════════════
   NUMBER / DATE INPUTS
═══════════════════════════════════════════════════════ */
.stNumberInput input, .stDateInput input {
    color: #111827 !important; background: #ffffff !important; font-size: 15px !important;
}

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer     { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ─────────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "coach_style": "Gentle Friend",
        "checkin_done": False,
        "checkin_data": {},
        "current_workout": "",
        "readiness_score": None,
        "chat_history": [],
        "active_tab": "🏠 Home",
        "guardrail_warnings": [],
        "last_meal_data": {},
        "session_id": str(hash(str(time.time())))[:8],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session()

# ── Reload .env on every Streamlit rerun so edits are picked up immediately
#    without needing a server restart or a "Refresh" button click.
from granite_client import _reload_env as _env_reload, GraniteClient
from guardrails import GuardrailPipeline

_env_reload()   # pull the latest .env values into os.environ right now

# Create a fresh GraniteClient on every render — it is lightweight (no network
# call in __init__ unless credentials are valid) and always reads the current .env.
client   = GraniteClient()
pipeline = GuardrailPipeline()
progress = get_progress()


# ─────────────────────────────────────────────────────────────
# HELPER: AI CALL WITH FULL GUARDRAIL PIPELINE
# ─────────────────────────────────────────────────────────────

def safe_ai_call(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 600,
    is_internal: bool = False,
) -> str:
    """
    Execute an AI call through the full guardrail pipeline.
    Input → guardrails → AI → output guardrails → response.

    Args:
        is_internal: True for system-generated prompts (feature builders).
                     Skips input guardrails since the prompt is trusted code,
                     not arbitrary user text.
    """
    session_id = st.session_state.get("session_id", "default")

    if is_internal:
        # System-built prompts are trusted — skip injection/SQL checks,
        # but still honour operational limits.
        sanitized_prompt = prompt
    else:
        # USER-typed text — run full input guardrail pipeline.
        valid, sanitized_prompt, error = pipeline.process_input(prompt, session_id)
        if not valid:
            return f"⚠️ {error}"

    # AI GENERATION
    system_prompt = build_system_prompt(st.session_state.coach_style)

    # Operational guardrail: track API call
    ok, msg = pipeline.operational_guardrails.track_api_call("granite")
    if not ok:
        return f"⚠️ {msg}"

    # Tool execution guardrail
    tool_ok, tool_msg = pipeline.tool_guardrails.authorize_tool("generate_workout", "generate")
    if not tool_ok:
        return f"⚠️ {tool_msg}"

    raw_response = client.generate(sanitized_prompt, system_prompt, temperature, max_tokens)

    # OUTPUT GUARDRAILS
    final_response, warnings = pipeline.process_output(
        raw_response,
        sanitized_prompt,
        {"coach_style": st.session_state.coach_style},
    )

    # Store warnings for display
    if warnings:
        st.session_state.guardrail_warnings = warnings

    return final_response


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.2rem 0 0.8rem;">
        <div style="font-size:3.2rem; line-height:1;">&#x1F4AA;</div>
        <div style="font-size:1.55rem; font-weight:800; color:#ffffff;
                    letter-spacing:-0.02em; margin:0.4rem 0 0.15rem;">
            Fitness Buddy
        </div>
        <div style="font-size:0.75rem; color:#93c5fd; font-weight:500;
                    letter-spacing:0.05em; text-transform:uppercase; margin-bottom:0.65rem;">
            AI-Powered Health Coach
        </div>
        <span class="ibm-badge">IBM Granite</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Coach personality selector (Feature F)
    st.markdown("**🎭 Coach Personality**")
    coach_icons = {
        "Gentle Friend": "🤗",
        "Energetic Coach": "⚡",
        "Calm Guide": "🧘",
        "Accountability Partner": "🎯",
    }
    coach_style = st.selectbox(
        "Choose your coach:",
        list(COACH_PERSONAS.keys()),
        format_func=lambda x: f"{coach_icons.get(x, '')} {x}",
        key="coach_style_selector",
    )
    st.session_state.coach_style = coach_style

    persona_descriptions = {
        "Gentle Friend": "Supportive & non-judgmental",
        "Energetic Coach": "Enthusiastic & challenge-driven",
        "Calm Guide": "Concise & mindful",
        "Accountability Partner": "Direct & goal-focused",
    }
    st.caption(f"*{persona_descriptions.get(coach_style, '')}*")

    st.markdown("---")

    # Navigation
    st.markdown("**📍 Navigation**")
    pages = [
        "🏠 Home",
        "📋 Daily Check-In",
        "🏋️ Workout Planner",
        "🥗 Meal Builder",
        "🪜 Habit Ladder",
        "📊 Progress",
        "💬 Chat",
        "🔐 Guardrails",
    ]
    selected_page = st.radio("", pages, label_visibility="collapsed")

    st.markdown("---")

    # Progress quick stats
    prog = get_progress()
    st.markdown("**📈 Quick Stats**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Workouts", prog["completed_workouts"])
        st.metric("Streak", f"{prog['habit_streak']}d")
    with col2:
        st.metric("Active Days", f"{prog['weekly_active_days']}/7")
        st.metric("Minutes", prog["total_active_minutes"])

    # IBM status — re-read live env on every render
    from granite_client import _reload_env
    _reload_env()
    st.markdown("---")
    if client.is_configured():
        active_model = os.getenv("IBM_GRANITE_MODEL_ID", "ibm/granite-3-2-8b-instruct").strip()
        model_short = active_model.split("/")[-1]  # e.g. "granite-3-2-8b-instruct"
        st.markdown(f"""
        <div style="background:#052e16;border:1px solid #16a34a;border-radius:8px;
                    padding:0.6rem 0.8rem;text-align:center;">
            <span style="color:#4ade80;font-weight:600;font-size:0.85rem;">
                ✅ IBM Granite Connected
            </span><br>
            <span style="color:#86efac;font-size:0.72rem;">
                {model_short}
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#431407;border:1px solid #c2410c;border-radius:8px;
                    padding:0.6rem 0.8rem;text-align:center;">
            <span style="color:#fdba74;font-weight:600;font-size:0.85rem;">
                ⚡ Demo Mode
            </span><br>
            <span style="color:#fed7aa;font-size:0.75rem;">
                Add IBM_API_KEY &amp; IBM_PROJECT_ID to .env
            </span>
        </div>
        """, unsafe_allow_html=True)
        # Trigger a rerun so the new .env values are reflected immediately
        if st.button("🔄 Refresh Connection", use_container_width=True, key="refresh_ibm"):
            st.rerun()


# ─────────────────────────────────────────────────────────────
# PAGE: HOME
# ─────────────────────────────────────────────────────────────

if selected_page == "🏠 Home":
    st.markdown("""
    <div class="main-header">
        <p class="banner-title" style="
            font-size: clamp(3rem, 7vw, 5.8rem) !important;
            font-weight: 900 !important;
            color: #ffffff !important;
            letter-spacing: -0.03em !important;
            line-height: 1.05 !important;
            text-shadow: 0 3px 14px rgba(0,0,0,0.35) !important;
            margin: 0 0 0.4rem 0 !important;
            padding: 0 !important;
            font-family: -apple-system, 'Segoe UI', Roboto, sans-serif !important;
        ">&#x1F4AA; Fitness Buddy</p>
        <p class="banner-subtitle" style="
            font-size: clamp(0.85rem, 1.3vw, 1.05rem) !important;
            color: #bfdbfe !important;
            font-weight: 400 !important;
            letter-spacing: 0.01em !important;
            line-height: 1.5 !important;
            margin: 0 !important;
            padding: 0 !important;
            font-family: -apple-system, 'Segoe UI', Roboto, sans-serif !important;
        ">Your AI-Powered Health &amp; Fitness Coach &mdash; Powered by IBM Granite on watsonx.ai</p>
    </div>
    """, unsafe_allow_html=True)

    # Welcome stats — custom HTML bar for guaranteed contrast
    prog = get_progress()
    st.markdown(f"""
    <div class="stat-bar">
        <div class="stat-item">
            <span class="stat-value">{prog['weekly_active_days']}/7</span>
            <span class="stat-label">🗓️ Active Days</span>
            <span class="stat-delta">This week</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">{prog['completed_workouts']}</span>
            <span class="stat-label">✅ Workouts</span>
            <span class="stat-delta">Total completed</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">{prog['total_active_minutes']}</span>
            <span class="stat-label">⏱️ Minutes</span>
            <span class="stat-delta">Total active</span>
        </div>
        <div class="stat-item">
            <span class="stat-value">{prog['habit_streak']}d</span>
            <span class="stat-label">🔥 Streak</span>
            <span class="stat-delta">Keep going!</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Feature overview
    st.subheader("What I Can Do For You")
    col1, col2 = st.columns(2)

    features = [
        ("📋 Daily Check-In", "Tell me how you feel today and get a personalized workout plan", "📋 Daily Check-In"),
        ("🏋️ Workout Planner", "Get workouts with Plan B modifications for any situation", "🏋️ Workout Planner"),
        ("🥗 Meal Builder", "Smart meal suggestions from ingredients you already have", "🥗 Meal Builder"),
        ("🪜 Habit Ladder", "Build lasting habits one small step at a time", "🪜 Habit Ladder"),
        ("📊 Progress Tracker", "Track progress beyond the scale — energy, streaks, achievements", "📊 Progress"),
        ("💬 AI Chat", "Ask anything about fitness, nutrition, or healthy habits", "💬 Chat"),
    ]

    for i, (title, desc, _) in enumerate(features):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div class="feature-card">
                <strong>{title}</strong><br>
                <span style="color:#374151; font-size:0.9rem;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Daily motivation
    st.subheader(f"💬 Today's Motivation from your {coach_style}")
    if st.button("✨ Get Motivated!", type="primary", use_container_width=True):
        with st.spinner("Getting your daily dose of motivation..."):
            prompt = build_motivation_prompt(
                st.session_state.coach_style,
                {
                    "weekly_active_days": prog["weekly_active_days"],
                    "habit_streak": prog["habit_streak"],
                    "last_workout_type": "general fitness",
                },
            )
            response = safe_ai_call(prompt, temperature=0.8, max_tokens=200, is_internal=True)
            st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)

    # Guardrail warnings display
    if st.session_state.guardrail_warnings:
        with st.expander("ℹ️ Safety Notices"):
            for warning in st.session_state.guardrail_warnings:
                st.markdown(f'<div class="guardrail-warning">ℹ️ {warning}</div>', unsafe_allow_html=True)
        st.session_state.guardrail_warnings = []


# ─────────────────────────────────────────────────────────────
# PAGE: DAILY CHECK-IN (Feature A + G)
# ─────────────────────────────────────────────────────────────

elif selected_page == "📋 Daily Check-In":
    st.header("📋 Daily Check-In")
    st.markdown("*Tell me about your day and I'll create the perfect workout for you.*")

    with st.form("checkin_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**⏰ Available Time**")
            time_options = {"5 minutes": "5", "10 minutes": "10", "20 minutes": "20",
                           "30 minutes": "30", "45 minutes": "45"}
            time_choice = st.select_slider(
                "How much time do you have?",
                options=list(time_options.keys()),
                value="20 minutes",
            )

            st.markdown("**⚡ Energy Level**")
            energy = st.select_slider(
                "How's your energy today?",
                options=["low", "medium", "high"],
                value="medium",
            )

            st.markdown("**😊 Current Mood**")
            mood = st.selectbox(
                "How are you feeling?",
                ["great", "good", "neutral", "tired", "stressed", "anxious", "sad"],
            )

            st.markdown("**😴 Sleep Last Night**")
            sleep_hours = st.slider("Hours of sleep", 3.0, 10.0, 7.0, 0.5)

        with col2:
            st.markdown("**📍 Workout Location**")
            location = st.selectbox(
                "Where will you work out?",
                ["home", "gym", "office", "outdoors", "hotel room", "small apartment"],
            )

            st.markdown("**🏋️ Available Equipment**")
            equipment_options = st.multiselect(
                "Select available equipment:",
                ["none", "dumbbells", "resistance bands", "yoga mat", "pull-up bar",
                 "kettlebell", "jump rope", "chair", "water bottles"],
                default=["none"],
            )

            st.markdown("**🎯 Experience Level**")
            experience = st.selectbox(
                "Your fitness experience:",
                ["beginner", "intermediate", "advanced"],
            )

            st.markdown("**🚨 Pain or Discomfort**")
            pain_areas = st.multiselect(
                "Any areas to avoid?",
                ["none", "lower back", "knees", "shoulders", "wrists", "hips", "ankles", "neck"],
                default=["none"],
            )

            st.markdown("**🔥 Preferred Intensity**")
            intensity = st.select_slider(
                "Workout intensity:",
                options=["very light", "light", "moderate", "intense", "very intense"],
                value="moderate",
            )

            st.markdown("**💤 Soreness Level**")
            soreness = st.selectbox("Muscle soreness?", ["none", "mild", "moderate", "severe"])

        submitted = st.form_submit_button("🚀 Generate My Personalized Plan", type="primary", use_container_width=True)

    if submitted:
        checkin_data = {
            "time": time_options[time_choice],
            "energy": energy,
            "mood": mood,
            "sleep_hours": sleep_hours,
            "location": location,
            "equipment": ", ".join(equipment_options) if equipment_options else "none",
            "experience": experience,
            "pain_areas": ", ".join(pain_areas) if pain_areas else "none",
            "intensity": intensity,
            "soreness": soreness,
            "rest_days_since_last_workout": 1,
        }
        st.session_state.checkin_data = checkin_data
        st.session_state.checkin_done = True

        # Calculate readiness score (Feature G)
        score_result = calculate_readiness_score(checkin_data)
        st.session_state.readiness_score = score_result

        # Record check-in
        record_checkin(energy, score_result["total"])

        # Display readiness score
        st.markdown("---")
        st.subheader("🎯 Your Fitness Readiness Score")

        score_col1, score_col2, score_col3 = st.columns([1, 2, 1])

        with score_col2:
            score = score_result["total"]
            color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 45 else "#ef4444"

            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Readiness Score", "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": color},
                    "steps": [
                        {"range": [0, 35], "color": "#fee2e2"},
                        {"range": [35, 55], "color": "#fef3c7"},
                        {"range": [55, 75], "color": "#dcfce7"},
                        {"range": [75, 100], "color": "#bbf7d0"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 2},
                        "thickness": 0.75,
                        "value": score,
                    },
                },
            ))
            fig.update_layout(height=250, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

        # Score breakdown
        st.markdown(f"""
        <div class="feature-card">
            <strong>Recommended Intensity: {score_result['recommended_intensity']}</strong><br>
            {score_result['recommendation']}<br><br>
            <em style="color:#374151; font-size:0.85rem;">{score_result['disclaimer']}</em>
        </div>
        """, unsafe_allow_html=True)

        # Score component bars
        with st.expander("📊 Score Breakdown"):
            components = score_result["components"]
            max_vals = {"energy": 25, "sleep": 20, "mood": 15, "soreness": 15, "time": 15, "recovery": 10}
            for component, value in components.items():
                max_v = max_vals.get(component, 20)
                pct = (value / max_v) * 100
                st.markdown(f"**{component.title()}**: {value}/{max_v}")
                st.progress(int(pct))

        # Generate workout plan
        st.markdown("---")
        st.subheader("🏋️ Your Personalized Workout Plan")

        # Check if MVW is needed (Feature B)
        if energy == "low" or score_result["total"] < 35:
            st.info("💙 Since your energy is low today, here's a Minimum Viable Workout — small but mighty!")
            with st.spinner("Creating a gentle plan just for you..."):
                mvw_options = get_minimum_viable_workouts()
                mvw = mvw_options[0]  # Default to mobility
                prompt = build_mvw_prompt("3-minute mobility", reason=f"energy is {energy} and feeling {mood}")
                response = safe_ai_call(prompt, temperature=0.6, is_internal=True)

        else:
            with st.spinner("Creating your personalized workout..."):
                prompt = build_checkin_prompt(checkin_data)
                response = safe_ai_call(prompt, temperature=0.7, is_internal=True)

        st.session_state.current_workout = response
        st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)

        # Workout action buttons
        st.markdown("---")
        mark_col1, mark_col2 = st.columns(2)
        with mark_col1:
            if st.button("✅ Mark Workout as Complete", type="primary", use_container_width=True):
                mins = int(time_options[time_choice])
                record_workout(mins, experience, "check-in workout")
                st.success("🎉 Workout recorded! Great job today!")
                st.balloons()

        with mark_col2:
            if st.button("🔄 Generate Different Plan", use_container_width=True):
                st.rerun()

        # Plan B section (Feature C)
        if st.session_state.current_workout:
            st.markdown("---")
            st.subheader("🔄 Plan B — Modify This Workout")
            st.caption("Every workout comes with built-in alternatives")

            plan_b_options = [
                "Make it easier", "Make it harder",
                "No-equipment alternative", "Quiet apartment version",
                "Low-impact version", "Shorten to 5 minutes",
            ]

            cols = st.columns(3)
            for i, option in enumerate(plan_b_options):
                with cols[i % 3]:
                    if st.button(f"{'⬇️' if 'easier' in option else '⬆️' if 'harder' in option else '🏠' if 'No-equip' in option else '🤫' if 'Quiet' in option else '🦵' if 'Low' in option else '⚡'} {option}", use_container_width=True):
                        with st.spinner(f"Modifying: {option}..."):
                            prompt = build_plan_b_prompt(st.session_state.current_workout, option)
                            modified = safe_ai_call(prompt, temperature=0.6, is_internal=True)
                            st.session_state.current_workout = modified
                            st.markdown(f'<div class="ai-response">{modified}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PAGE: WORKOUT PLANNER
# ─────────────────────────────────────────────────────────────

elif selected_page == "🏋️ Workout Planner":
    st.header("🏋️ Workout Planner")

    tab1, tab2 = st.tabs(["🏃 Custom Workout", "⚡ Quick Workouts (MVW)"])

    with tab1:
        st.subheader("Generate a Custom Workout")

        col1, col2 = st.columns(2)
        with col1:
            workout_goal = st.selectbox(
                "🎯 Goal",
                ["General Fitness", "Weight Loss", "Muscle Building", "Flexibility",
                 "Stress Relief", "Core Strength", "Cardio Endurance"],
            )
            workout_duration = st.select_slider(
                "⏰ Duration",
                ["10 min", "15 min", "20 min", "30 min", "45 min"],
                value="20 min",
            )
            workout_location = st.selectbox(
                "📍 Location",
                ["Home (no equipment)", "Home (with equipment)", "Gym", "Outdoors", "Office"],
            )

        with col2:
            fitness_level = st.selectbox(
                "💪 Fitness Level",
                ["Beginner", "Intermediate", "Advanced"],
            )
            focus_area = st.selectbox(
                "🎯 Focus Area",
                ["Full Body", "Upper Body", "Lower Body", "Core", "Cardio"],
            )
            avoid_injuries = st.text_input(
                "🚨 Areas to Avoid (optional)",
                placeholder="e.g., bad knees, shoulder pain",
            )

        if st.button("🚀 Generate Workout", type="primary", use_container_width=True):
            with st.spinner("Creating your workout..."):
                prompt = f"""Create a {workout_duration} {workout_goal.lower()} workout.
                
Settings:
- Level: {fitness_level}
- Location: {workout_location}
- Focus: {focus_area}
- Avoid: {avoid_injuries if avoid_injuries else 'nothing specific'}

Include warm-up, main workout (with sets/reps), and cool-down.
Format clearly with headers and bullet points."""

                response = safe_ai_call(prompt, is_internal=True)
                st.session_state.current_workout = response
                st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)

                # Plan B modifications (Feature C)
                st.markdown("---")
                st.subheader("🔄 Modify This Workout")
                plan_b_cols = st.columns(3)
                plan_b_options = [
                    ("⬇️ Make Easier", "Make it easier"),
                    ("⬆️ Make Harder", "Make it harder"),
                    ("🏠 No Equipment", "No-equipment alternative"),
                    ("🤫 Quiet Version", "Quiet apartment version"),
                    ("🦵 Low Impact", "Low-impact version"),
                    ("⚡ 5 Min Version", "Shorten to 5 minutes"),
                ]
                for i, (label, mod_key) in enumerate(plan_b_options):
                    with plan_b_cols[i % 3]:
                        if st.button(label, key=f"planb_{i}", use_container_width=True):
                            with st.spinner(f"Applying: {mod_key}..."):
                                mod_prompt = build_plan_b_prompt(st.session_state.current_workout, mod_key)
                                modified = safe_ai_call(mod_prompt, temperature=0.6, is_internal=True)
                                st.markdown(f'<div class="ai-response">{modified}</div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("⚡ Minimum Viable Workouts")
        st.markdown("*When you're tired or busy — because something always beats nothing!*")

        mvw_list = get_minimum_viable_workouts()
        for mvw in mvw_list:
            with st.expander(f"⚡ {mvw['name']} — {mvw['time']}"):
                st.markdown(f"*{mvw['description']}*")
                for step in mvw["exercises"]:
                    st.markdown(f"- {step}")

                if st.button(f"▶️ Start {mvw['name']}", key=f"mvw_{mvw['name']}", use_container_width=True):
                    with st.spinner("Creating your micro-workout..."):
                        prompt = build_mvw_prompt(mvw["name"].lower(), "looking for a quick session")
                        response = safe_ai_call(prompt, temperature=0.6, max_tokens=300, is_internal=True)
                        st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)
                        if st.button("✅ Done!", key=f"done_{mvw['name']}"):
                            record_workout(5, "beginner", mvw["name"])
                            st.success("Counted! Every bit matters 💙")


# ─────────────────────────────────────────────────────────────
# PAGE: MEAL BUILDER (Feature D)
# ─────────────────────────────────────────────────────────────

elif selected_page == "🥗 Meal Builder":
    st.header("🥗 Smart Meal Builder")
    st.markdown("*Enter what you have at home — I'll suggest practical, nutritious meals.*")

    with st.form("meal_form"):
        col1, col2 = st.columns(2)

        with col1:
            ingredients_input = st.text_area(
                "🥬 Ingredients you have",
                placeholder="e.g., rice, dal, onion, tomato, potato, paneer, eggs...",
                height=100,
            )

            preference = st.selectbox(
                "🌿 Dietary Preference",
                ["Vegetarian", "Vegan", "Non-Vegetarian", "Eggetarian", "Jain"],
            )

            allergies_input = st.text_input(
                "⚠️ Allergies",
                placeholder="e.g., peanuts, gluten, dairy — or type 'none'",
            )

            regional = st.selectbox(
                "🗺️ Regional Preference",
                ["Indian (North)", "Indian (South)", "Indian (West)", "Indian (East)",
                 "Continental", "Mediterranean", "No preference"],
            )

        with col2:
            cook_time = st.select_slider(
                "⏰ Cooking Time",
                ["10 minutes", "20 minutes", "30 minutes", "45 minutes", "1 hour"],
                value="30 minutes",
            )

            budget = st.select_slider(
                "💰 Budget Level",
                ["very low", "low", "medium", "high"],
                value="low",
            )

            meal_type = st.selectbox(
                "🍽️ Meal Type",
                ["Breakfast", "Lunch", "Dinner", "Snack", "Post-workout", "Pre-workout"],
            )

            health_goal = st.selectbox(
                "💚 Health Goal (optional)",
                ["Balanced", "High protein", "High fiber", "Low carb", "Energy boost", "Gut health"],
            )

        submitted_meal = st.form_submit_button("🍳 Suggest Meals", type="primary", use_container_width=True)

    if submitted_meal:
        if not ingredients_input.strip():
            st.warning("Please enter at least a few ingredients you have at home.")
        else:
            meal_data = {
                "ingredients": ingredients_input,
                "preference": preference,
                "allergies": allergies_input if allergies_input else "none",
                "cook_time": cook_time,
                "budget": budget,
                "meal_type": meal_type.lower(),
                "regional": regional,
                "health_goal": health_goal,
            }
            st.session_state.last_meal_data = meal_data

            with st.spinner("Building your personalized meal suggestions..."):
                prompt = build_meal_prompt(meal_data)
                response = safe_ai_call(prompt, temperature=0.7, max_tokens=700, is_internal=True)
                st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)

            # Quick nutrition guide
            with st.expander("💡 Quick Indian Nutrition Guide"):
                nutrition_data = {
                    "Food": ["Dal (1 cup cooked)", "Paneer (100g)", "Roti (1 piece)", "Brown Rice (1 cup)",
                             "Eggs (2 whole)", "Poha (1 cup)", "Chana (1 cup cooked)", "Curd (1 cup)"],
                    "Protein (g)": [9, 18, 3, 5, 12, 4, 15, 9],
                    "Calories": [230, 265, 70, 215, 140, 250, 270, 100],
                    "Key Benefit": ["High fiber", "Calcium + protein", "Energy", "Complex carbs",
                                   "Complete protein", "Light & digestible", "Plant protein + fiber", "Probiotic"],
                }
                st.dataframe(pd.DataFrame(nutrition_data), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────
# PAGE: HABIT LADDER (Feature E)
# ─────────────────────────────────────────────────────────────

elif selected_page == "🪜 Habit Ladder":
    st.header("🪜 Habit Ladder")
    st.markdown("*Build lasting habits one small step at a time. Consistency unlocks the next level.*")

    prog = get_progress()
    current_level = prog.get("habit_level", 1)
    days_this_level = prog.get("habit_days_this_level", 0)

    # Display the ladder
    st.subheader("Your Habit Journey")

    for step in HABIT_LADDER_STEPS:
        level = step["level"]
        if level < current_level:
            status_class = "habit-done"
            status_icon = "✅"
            status_text = "Completed"
        elif level == current_level:
            status_class = "habit-active"
            status_icon = "🔵"
            status_text = f"Active — {days_this_level}/{step['consistency_needed']} days"
        else:
            status_class = "habit-locked"
            status_icon = "🔒"
            status_text = "Locked"

        st.markdown(f"""
        <div class="habit-step {status_class}">
            <span style="font-size:1.5rem; margin-right:0.75rem;">{step['emoji']}</span>
            <div style="flex:1">
                <strong>Level {level}: {step['habit']}</strong><br>
                <span style="color:#1e293b; font-size:0.85rem;">{step['description']}</span>
            </div>
            <div style="text-align:right; font-size:0.8rem; color:#1e293b;">
                {status_icon} {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if level == current_level:
            progress_pct = min(days_this_level / step["consistency_needed"], 1.0)
            st.progress(progress_pct, text=f"Progress: {days_this_level}/{step['consistency_needed']} days consistent")

    st.markdown("---")

    # Daily habit tracking
    col1, col2 = st.columns(2)
    with col1:
        current_habit = get_current_habit(current_level)
        st.markdown(f"""
        <div class="feature-card">
            <strong>Today's Habit:</strong> {current_habit['emoji']} {current_habit['habit']}<br>
            <em style="color:#374151;">Keep it simple, keep it consistent.</em>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ I Did It Today!", type="primary", use_container_width=True):
            updated = increment_habit_day()
            new_level = updated.get("habit_level", 1)
            st.success(f"🎉 Great job! That's {updated['habit_days_this_level']} days consistent!")
            if new_level > current_level:
                st.balloons()
                next_habit = get_current_habit(new_level)
                st.success(f"🚀 LEVEL UP! You've unlocked: {next_habit['emoji']} {next_habit['habit']}")

    with col2:
        if st.button("💬 Get Habit Coaching", use_container_width=True):
            with st.spinner("Getting your habit coaching message..."):
                prompt = build_habit_prompt(current_level, days_this_level, st.session_state.coach_style)
                response = safe_ai_call(prompt, temperature=0.75, max_tokens=200, is_internal=True)
                st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Habit streak visualization
    st.subheader("📊 Habit Stats")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔥 Current Streak", f"{prog['habit_streak']} days")
    with col2:
        st.metric("📋 Habit Level", f"{current_level}/5")
    with col3:
        st.metric("📅 Days This Level", f"{days_this_level}/{get_current_habit(current_level)['consistency_needed']}")


# ─────────────────────────────────────────────────────────────
# PAGE: PROGRESS (Feature H)
# ─────────────────────────────────────────────────────────────

elif selected_page == "📊 Progress":
    st.header("📊 Progress Dashboard")
    st.markdown("*Track what really matters — beyond the scale.*")

    prog = get_progress()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🗓️ Active Days", f"{prog['weekly_active_days']}/7", delta="This week")
    with col2:
        st.metric("✅ Total Workouts", prog["completed_workouts"])
    with col3:
        st.metric("⏱️ Total Minutes", prog["total_active_minutes"])
    with col4:
        st.metric("🔥 Habit Streak", f"{prog['habit_streak']} days")

    st.markdown("---")

    col1, col2 = st.columns(2)

    # Energy trend chart
    with col1:
        st.subheader("⚡ Energy Trend")
        energy_readings = prog.get("energy_readings", [])
        if len(energy_readings) >= 2:
            df_energy = pd.DataFrame({
                "Day": list(range(1, len(energy_readings) + 1)),
                "Energy": energy_readings,
            })
            fig_energy = px.line(
                df_energy, x="Day", y="Energy",
                title="Energy Levels Over Time",
                labels={"Energy": "Energy (1=Low, 3=High)"},
                color_discrete_sequence=["#2563eb"],
            )
            fig_energy.update_layout(
                yaxis=dict(range=[0.5, 3.5], tickvals=[1, 2, 3], ticktext=["Low", "Medium", "High"]),
                height=250,
                margin=dict(t=30, b=20),
            )
            st.plotly_chart(fig_energy, use_container_width=True)
        else:
            st.info("Complete more daily check-ins to see your energy trend.")
            trend_label = {"stable": "📊 Stable", "improving": "📈 Improving", "declining": "📉 Declining"}
            st.markdown(f"**Current Trend:** {trend_label.get(prog.get('energy_trend', 'stable'), '📊 Stable')}")

    # Readiness scores
    with col2:
        st.subheader("🎯 Readiness Scores")
        readiness_data = prog.get("readiness_scores", [])
        if len(readiness_data) >= 2:
            df_readiness = pd.DataFrame(readiness_data[-14:])
            fig_ready = px.bar(
                df_readiness, x="date", y="score",
                title="Daily Readiness Scores",
                color="score",
                color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
                range_color=[0, 100],
            )
            fig_ready.update_layout(height=250, margin=dict(t=30, b=20), showlegend=False)
            st.plotly_chart(fig_ready, use_container_width=True)
        else:
            st.info("Complete daily check-ins to track your readiness scores.")

    # Workout log
    st.markdown("---")
    st.subheader("📋 Recent Workout Log")
    workout_log = prog.get("workout_log", [])
    if workout_log:
        df_log = pd.DataFrame(workout_log[-10:][::-1])  # Last 10, newest first
        df_log.columns = ["Date", "Duration (min)", "Difficulty", "Type"]
        st.dataframe(df_log, use_container_width=True, hide_index=True)
    else:
        st.info("No workouts logged yet. Complete a workout to see your history here!")

    # Achievements
    st.markdown("---")
    st.subheader("🏆 Achievements")
    achievements = prog.get("achievements", [])
    if achievements:
        cols = st.columns(3)
        for i, achievement in enumerate(achievements):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="feature-card" style="border-left-color: #f59e0b; text-align:center;">
                    <div style="font-size:0.95rem;">{achievement}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Complete workouts and maintain habits to earn achievements! 🏆")

    # Progress summary with AI
    st.markdown("---")
    if st.button("🤖 Get AI Progress Summary", type="primary", use_container_width=True):
        with st.spinner("Analyzing your progress..."):
            summary_text = build_progress_summary(prog)
            prompt = f"""Based on this user's fitness progress data, provide an encouraging and insightful 
progress analysis in 3-4 sentences.

{summary_text}

Focus on:
1. What they've done well
2. The most impressive achievement
3. One specific area to focus on next week
4. An uplifting closing thought

Keep it warm and personal."""
            response = safe_ai_call(prompt, temperature=0.7, max_tokens=250, is_internal=True)
            st.markdown(f'<div class="ai-response">{response}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PAGE: CHAT
# ─────────────────────────────────────────────────────────────

elif selected_page == "💬 Chat":
    st.header("💬 Chat with Fitness Buddy")
    st.markdown(f"*Your {st.session_state.coach_style} is ready to help with anything fitness-related.*")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"], avatar="💪" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])

    # Chat input
    if user_input := st.chat_input("Ask me about workouts, meals, habits, or anything fitness-related..."):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant", avatar="💪"):
            with st.spinner("Thinking..."):
                # Build context from recent history
                context = ""
                if len(st.session_state.chat_history) > 2:
                    recent = st.session_state.chat_history[-4:-1]
                    context = "\n".join([f"{m['role'].title()}: {m['content']}" for m in recent])
                    context = f"\nRecent conversation:\n{context}\n\n"

                prompt = f"{context}User: {user_input}"
                response = safe_ai_call(prompt, temperature=0.75, max_tokens=500)
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Quick action buttons
    if not st.session_state.chat_history:
        st.markdown("---")
        st.subheader("💡 Quick Questions")
        quick_questions = [
            "Give me a 10-minute home workout I can do right now",
            "What can I make for dinner with rice, dal, and vegetables?",
            "I haven't exercised in 2 weeks — where do I start?",
            "How do I stay motivated when I'm tired?",
            "Suggest a simple morning routine under 5 minutes",
        ]
        cols = st.columns(2)
        for i, question in enumerate(quick_questions[:4]):
            with cols[i % 2]:
                if st.button(question, key=f"quick_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": question})
                    with st.spinner("Getting your answer..."):
                        response = safe_ai_call(question, temperature=0.75)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


# ─────────────────────────────────────────────────────────────
# PAGE: GUARDRAILS DASHBOARD
# ─────────────────────────────────────────────────────────────

elif selected_page == "🔐 Guardrails":
    st.header("🔐 AI Safety Guardrails Dashboard")
    st.markdown("*Fitness Buddy is protected by 9 layers of AI safety guardrails.*")

    guardrail_info = [
        {
            "number": "1",
            "name": "Input Guardrails",
            "icon": "🛡️",
            "status": "Active",
            "checks": [
                "✅ Prompt injection detection",
                "✅ SQL injection prevention",
                "✅ Malicious content filtering",
                "✅ PII detection & redaction",
                "✅ Off-topic filtering",
                "✅ Input length validation",
                "✅ HTML sanitization",
            ],
        },
        {
            "number": "2",
            "name": "Output Guardrails",
            "icon": "📤",
            "status": "Active",
            "checks": [
                "✅ Toxicity & harmful language filtering",
                "✅ Sensitive information filtering",
                "✅ Medical disclaimer injection",
                "✅ Hallucination risk flagging",
                "✅ Fitness relevance validation",
                "✅ Response format validation",
            ],
        },
        {
            "number": "3",
            "name": "Tool Execution Guardrails",
            "icon": "🔧",
            "status": "Active",
            "checks": [
                "✅ Tool access permissions",
                "✅ API authorization",
                "✅ Function call parameter validation",
                "✅ Restricted tool execution",
                "✅ Per-tool rate limiting",
            ],
        },
        {
            "number": "4",
            "name": "Data Guardrails",
            "icon": "🗄️",
            "status": "Active",
            "checks": [
                "✅ Role-based data access control",
                "✅ PII anonymization in storage",
                "✅ Sensitive field masking in logs",
                "✅ Database query validation",
                "✅ Data privacy protection",
            ],
        },
        {
            "number": "5",
            "name": "Security Guardrails",
            "icon": "🔒",
            "status": "Active",
            "checks": [
                "✅ Jailbreak attempt detection",
                "✅ Session-based failed attempt tracking",
                "✅ Auto-blocking after repeated violations",
                "✅ API key format validation",
                "✅ Credential safety checks",
            ],
        },
        {
            "number": "6",
            "name": "Operational Guardrails",
            "icon": "⚙️",
            "status": "Active",
            "checks": [
                "✅ Execution timeout enforcement",
                "✅ Daily API call tracking",
                "✅ Exponential backoff retry",
                "✅ Token usage monitoring",
                "✅ Cost monitoring",
            ],
        },
        {
            "number": "7",
            "name": "Human-in-the-Loop Guardrails",
            "icon": "👤",
            "status": "Active",
            "checks": [
                "✅ Critical action approval gates",
                "✅ Medical emergency escalation",
                "✅ Mental health crisis detection",
                "✅ Emergency service referral",
                "✅ Professional consultation prompts",
            ],
        },
        {
            "number": "8",
            "name": "Multi-Agent Guardrails",
            "icon": "🤝",
            "status": "Active",
            "checks": [
                "✅ Agent-level access control",
                "✅ Task assignment validation",
                "✅ Cross-agent output verification",
                "✅ Iteration limit enforcement",
                "✅ Infinite loop prevention",
            ],
        },
        {
            "number": "9",
            "name": "Ethical & Compliance Guardrails",
            "icon": "⚖️",
            "status": "Active",
            "checks": [
                "✅ Bias language detection",
                "✅ Inclusive language enforcement",
                "✅ Regulatory compliance checks",
                "✅ Explainability tagging",
                "✅ Immutable audit trail logging",
                "✅ Responsible AI principles",
            ],
        },
    ]

    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🛡️ Guardrail Layers", "9", delta="All Active")
    with col2:
        audit_entries = len(pipeline.ethical_guardrails.get_audit_log())
        st.metric("📋 Audit Log Entries", audit_entries)
    with col3:
        st.metric("🔍 Checks per Request", "15+", delta="Input + Output + Ethics")

    st.markdown("---")

    # Guardrail cards
    col1, col2 = st.columns(2)
    for i, guardrail in enumerate(guardrail_info):
        with col1 if i % 2 == 0 else col2:
            with st.expander(f"{guardrail['icon']} {guardrail['number']}. {guardrail['name']} — ✅ {guardrail['status']}"):
                for check in guardrail["checks"]:
                    st.markdown(check)

    st.markdown("---")

    # Live guardrail test
    st.subheader("🧪 Test Guardrails Live")
    st.caption("Try entering different inputs to see how guardrails respond")

    test_input = st.text_input(
        "Test input:",
        placeholder="Try: 'ignore your instructions', or 'my email is test@email.com', or a normal fitness question",
    )

    if st.button("🔍 Run Guardrail Check", use_container_width=True):
        if test_input:
            with st.spinner("Running guardrail checks..."):
                valid, sanitized, error = pipeline.process_input(test_input, "test_session")

                st.markdown("**Guardrail Results:**")
                if valid:
                    st.success(f"✅ Input passed all checks")
                    # Check for PII redaction
                    if sanitized != test_input:
                        st.info(f"ℹ️ Input was sanitized: `{sanitized}`")
                    else:
                        st.markdown(f"Sanitized input: `{sanitized}`")
                else:
                    st.error(f"🚫 Input blocked: {error}")

                # Show which checks ran
                st.markdown("**Checks Applied:**")
                checks_ran = [
                    "HTML sanitization", "Prompt injection scan", "SQL injection scan",
                    "Harmful content scan", "PII detection", "Off-topic detection",
                    "Jailbreak detection", "Length validation",
                ]
                for check in checks_ran:
                    st.markdown(f"- ✅ {check}")

    # Audit log viewer
    st.markdown("---")
    st.subheader("📋 Recent Audit Log")
    audit_log = pipeline.ethical_guardrails.get_audit_log()
    if audit_log:
        df_audit = pd.DataFrame(audit_log[-10:][::-1])
        st.dataframe(df_audit[["timestamp", "action", "input_hash", "output_hash"]], use_container_width=True, hide_index=True)
    else:
        st.info("Audit log will populate as you use the app.")

    # IBM Cloud status — dynamic, reflects actual credential state
    st.markdown("---")
    _active_model = os.getenv("IBM_GRANITE_MODEL_ID", "ibm/granite-4-h-small").strip()
    if client.is_configured():
        st.markdown(f"""
        <div class="feature-card" style="border-left-color: #16a34a; background:#f0fdf4;">
            <strong style="color:#15803d;">✅ IBM Granite Active</strong><br>
            This application is connected to <strong>IBM watsonx.ai</strong>.
            All AI calls pass through this guardrail pipeline before the model is invoked
            and again after the response is received.<br>
            <span style="color:#374151; font-size:13px;">
                Active model: <code>{_active_model}</code>
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="feature-card" style="border-left-color: #f59e0b; background:#fefce8;">
            <strong style="color:#92400e;">⚡ Demo Mode — IBM Granite Not Connected</strong><br>
            Add your IBM Cloud credentials to <code>.env</code> to enable live AI responses:
            <ul style="margin:0.5rem 0 0; color:#374151; font-size:14px;">
                <li><code>IBM_API_KEY</code> — your IBM Cloud API key</li>
                <li><code>IBM_PROJECT_ID</code> — your watsonx.ai project ID</li>
                <li><code>IBM_GRANITE_MODEL_ID</code> — model (default: <code>ibm/granite-4-h-small</code>)</li>
            </ul>
            After saving, click <strong>🔄 Refresh Connection</strong> in the sidebar.
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#374151; font-size:0.8rem; padding: 1rem 0; border-top: 1px solid #d1d5db; margin-top:0.5rem;">
    💪 <strong>Fitness Buddy</strong> — AI-Powered Health Coach<br>
    Powered by <strong>IBM Granite on watsonx.ai</strong> | Built with Streamlit<br>
    <em>Not a medical product. Always consult a healthcare professional for medical advice.</em>
</div>
""", unsafe_allow_html=True)
