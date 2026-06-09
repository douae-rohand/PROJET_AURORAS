import io
import os
import streamlit as st
import pandas as pd
import requests
import base64
import math
from datetime import datetime
from pathlib import Path

# =================================================================
# CONFIGURATION DE LA PAGE
# =================================================================
st.set_page_config(
    page_title="AURORA - Ethereal Space Weather ML",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =================================================================
# STYLE CSS "AURORA BOREALIS PREMIUM"
# =================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;500;600;700&display=swap');

    /* Reset global */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%) !important;
        font-family: 'Inter', sans-serif !important;
        color: #2d3748 !important;
    }

    .main .block-container,
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 0.35rem !important;
        padding-left: 6% !important;
        padding-right: 6% !important;
        max-width: 100% !important;
    }

    [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }
    [data-testid="stDecoration"] { display: none; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stToolbar"] { display: none; }

    /* Neutraliser les cadres Streamlit vides */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    /* Marqueurs invisibles pour ancrer le style sur les colonnes */
    .aurora-marker,
    .aurora-page-marker,
    .header-row-marker,
    .predict-grid-marker,
    .about-info-grid-marker,
    .about-metrics-grid-marker {
        display: none !important;
    }

    /* Panneaux glassmorphism — appliqués sur la colonne Streamlit */
    div[data-testid="column"]:has(.aurora-card-marker) > div[data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 24px;
        padding: 2.5rem 2rem;
        box-shadow: 0 15px 35px rgba(0,0,0,0.05);
        height: 100%;
    }

    div[data-testid="column"]:has(.info-card-marker) > div[data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.4);
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 20px;
        padding: 1.75rem;
        height: 100%;
    }

    div[data-testid="stHorizontalBlock"]:has(.predict-grid-marker),
    div[data-testid="stHorizontalBlock"]:has(.about-info-grid-marker),
    div[data-testid="stHorizontalBlock"]:has(.about-metrics-grid-marker) {
        align-items: stretch !important;
        gap: 1.5rem !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.predict-grid-marker) > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(.about-info-grid-marker) > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(.about-metrics-grid-marker) > div[data-testid="column"] {
        align-self: stretch !important;
    }

    /* Header — compact, collé en haut */
    div[data-testid="stHorizontalBlock"]:has(.header-row-marker) {
        margin-top: -0.75rem !important;
        align-items: center !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.header-row-marker) > div[data-testid="column"] {
        padding-top: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.header-row-marker) [data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
        padding-top: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.header-row-marker) [data-testid="stVerticalBlock"] > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.header-row-marker) .stButton > button {
        margin-top: 0 !important;
        padding-top: 6px !important;
        padding-bottom: 6px !important;
    }

    .header-logo-container {
        display: flex;
        align-items: center;
        padding: 0;
        margin-left: -35px;
        margin-top: -22px;
    }

    .logo-img {
        max-width: 130px;
        height: auto;
        filter: drop-shadow(0 0 12px rgba(128, 90, 213, 0.4));
    }

    .header-status {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding-top: 0;
        margin-top: -8px;
        height: 100%;
    }

    .status-badge {
        background: rgba(79, 209, 197, 0.1);
        border-radius: 20px;
        padding: 4px 12px;
        border: 1px solid rgba(79, 209, 197, 0.4);
        white-space: nowrap;
    }

    /* Navigation */
    .stButton > button[key^="nav"] {
        background: linear-gradient(135deg, #6b46c1 0%, #4fd1c5 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 6px 16px !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        box-shadow: 0 0 15px rgba(128, 90, 213, 0.3) !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
        width: 100% !important;
        min-width: 110px !important;
    }

    .stButton > button[key^="nav"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(79, 209, 197, 0.5) !important;
    }

    .nav-slot {
        min-height: 18px;
        text-align: center;
        margin-top: 6px;
    }

    .nav-active-label {
        font-size: 0.6rem;
        color: #319795;
        letter-spacing: 0.15em;
        font-weight: 600;
        text-transform: uppercase;
    }

    .nav-slot-spacer {
        display: block;
        height: 18px;
    }

    .header-divider {
        border: none;
        border-top: 1px solid rgba(0,0,0,0.05);
        margin: 0.25rem 0 2.5rem 0;
    }

    /* Sections */
    .section-intro {
        margin-bottom: 3rem;
    }

    .card-title {
        color: #1a202c;
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        margin-bottom: 1.75rem;
        margin-top: 0;
    }

    .card-title-sm {
        color: #1a202c;
        font-family: 'Playfair Display', serif;
        font-size: 1.2rem;
        margin: 2rem 0 1rem 0;
    }

    .inference-tag {
        color: #f6ad55;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.3em;
        margin-bottom: 0.8rem;
    }

    .main-title {
        font-family: 'Playfair Display', serif;
        color: #1a202c;
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        line-height: 1.2;
    }

    .main-title span {
        background: linear-gradient(135deg, #9f7aea 0%, #ed64a6 40%, #f6ad55 70%, #4fd1c5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .lead-text {
        color: #4a5568;
        font-size: 1.1rem;
        max-width: 720px;
        line-height: 1.7;
        margin-bottom: 0;
    }

    .info-mini-card h4 {
        color: #f6ad55;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        margin: 0 0 1rem 0;
    }

    .info-mini-card p {
        color: #4a5568;
        font-size: 0.98rem;
        line-height: 1.75;
        font-weight: 400;
        margin: 0;
    }

    /* Inputs */
    .input-label-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 0.35rem;
    }

    .input-label-row span:first-child {
        color: #4a5568;
        font-weight: 600;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .unit-tag {
        color: #4fd1c5;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .sub-help {
        color: #718096;
        font-size: 0.75rem;
        margin-bottom: 1.1rem;
        margin-top: 0.15rem;
    }

    .stNumberInput input,
    .stSelectbox [data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        color: #1a202c !important;
        border-radius: 12px !important;
    }

    .stNumberInput input {
        padding: 12px !important;
        font-size: 1rem !important;
    }

    .stNumberInput input:focus {
        border-color: #4fd1c5 !important;
        box-shadow: 0 0 10px rgba(79, 209, 197, 0.2) !important;
    }

    label p {
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stButton > button:not([key^="nav"]) {
        width: 100% !important;
        background: linear-gradient(90deg, #6b46c1 0%, #d53f8c 50%, #4fd1c5 100%) !important;
        color: white !important;
        border: none !important;
        padding: 18px !important;
        font-weight: 700 !important;
        border-radius: 16px !important;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        box-shadow: 0 10px 25px rgba(213, 63, 140, 0.3) !important;
        transition: all 0.4s ease !important;
        margin-top: 1.5rem !important;
    }

    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
    }

    .stButton > button:not([key^="nav"]):hover,
    .stDownloadButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(79, 209, 197, 0.5) !important;
    }

    .stDownloadButton > button {
        background: linear-gradient(90deg, #6b46c1 0%, #d53f8c 50%, #4fd1c5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        padding: 0.85rem 1.5rem !important;
        margin-top: 1rem !important;
    }

    /* Résultats */
    .prob-val {
        font-family: 'Playfair Display', serif;
        background: linear-gradient(135deg, #f6ad55, #4fd1c5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 5.5rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .status-pill {
        display: inline-block;
        padding: 0.45rem 1.25rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 1.25rem;
    }

    .status-high {
        background: rgba(237, 100, 166, 0.15);
        border: 1px solid rgba(237, 100, 166, 0.45);
        color: #ed64a6;
    }

    .status-low {
        background: rgba(79, 209, 197, 0.12);
        border: 1px solid rgba(79, 209, 197, 0.35);
        color: #4fd1c5;
    }

    .result-status {
        color: #1a202c;
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        margin-bottom: 0.75rem;
    }

    .result-meta {
        color: #4a5568;
        line-height: 1.7;
        max-width: 380px;
        margin: 0 auto;
        font-size: 0.95rem;
    }

    .result-panel {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
    }

    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 460px;
        text-align: center;
        padding: 1rem;
    }

    /* Batch upload */
    .upload-intro {
        color: #718096;
        font-size: 0.92rem;
        margin-bottom: 1.25rem;
        line-height: 1.7;
    }

    .upload-intro code {
        color: #a0aec0;
        font-size: 0.82rem;
    }

    .upload-zone-header {
        text-align: center;
        margin-bottom: 1rem;
        padding: 1.5rem 1rem 0.5rem 1rem;
        border: 1px dashed rgba(79, 209, 197, 0.4);
        border-radius: 20px 20px 0 0;
        background: linear-gradient(135deg, rgba(159, 122, 234, 0.08), rgba(79, 209, 197, 0.06));
    }

    .upload-zone-header .icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .upload-zone-header .title {
        color: #1a202c;
        font-family: 'Playfair Display', serif;
        font-size: 1.35rem;
    }

    div[data-testid="column"]:has(.upload-panel-marker) [data-testid="stFileUploader"] {
        margin-top: 0 !important;
    }

    div[data-testid="column"]:has(.upload-panel-marker) [data-testid="stFileUploader"] section {
        background: rgba(255, 255, 255, 0.4) !important;
        border: 1px dashed rgba(0, 0, 0, 0.15) !important;
        border-top: none !important;
        border-radius: 0 0 20px 20px !important;
        padding: 1.25rem !important;
        margin-bottom: 0.5rem !important;
    }

    .upload-hint {
        text-align: center;
        color: #718096;
        font-size: 0.88rem;
        margin-bottom: 1.5rem;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #9f7aea, #ed64a6, #f6ad55, #4fd1c5) !important;
    }

    /* Métriques */
    .metric-grid-item {
        background: rgba(255, 255, 255, 0.6);
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 20px;
        padding: 1.75rem 1.25rem;
        text-align: center;
        transition: border-color 0.3s;
        margin-bottom: 0.85rem;
        height: calc(50% - 0.5rem);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.02);
    }

    .metric-grid-item:hover { border-color: #4fd1c5; }
    .metric-title {
        font-size: 0.75rem;
        color: #718096;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
        letter-spacing: 0.1em;
    }
    .metric-val {
        font-size: 2.2rem;
        color: #1a202c;
        font-weight: 700;
        font-family: 'Playfair Display', serif;
    }

    .model-desc {
        color: #4a5568;
        font-size: 1rem;
        line-height: 1.8;
        margin-bottom: 1.5rem;
    }

    .model-footer-card {
        padding-top: 1.5rem;
        border-top: 1px solid rgba(0, 0, 0, 0.05);
    }

    .model-footer-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.85rem;
        font-size: 0.9rem;
    }

    .model-footer-label { color: #718096; }
    .model-footer-value { color: #1a202c; font-weight: 600; }
    .model-footer-status { color: #319795; font-weight: 600; }

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 16px;
        overflow: hidden;
    }

    .page-footer {
        text-align: center;
        padding: 3.5rem 0 2.5rem 0;
        color: #4a5568;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
    }

    @media (max-width: 900px) {
        .main .block-container { padding-left: 4% !important; padding-right: 4% !important; }
        .main-title { font-size: 2.4rem; }
        .prob-val { font-size: 4rem; }
    }
</style>
""", unsafe_allow_html=True)

# =================================================================
# CONSTANTES & API
# =================================================================
API_BASE_URL = os.getenv("AURORA_API_URL", "http://localhost:8000").rstrip("/")
API_TIMEOUT = int(os.getenv("AURORA_API_TIMEOUT", "60"))

# Colonnes minimales attendues côté CSV (maintenant uniquement les données brutes)
REQUIRED_BATCH_COLUMNS = [
    "solar_wind_speed",
    "solar_wind_density",
    "bz_component",
    "dst_index",
    "month",
    "season",
    "hour_interval",
    "is_solar_maximum",
]

CONFIDENCE_FR = {"high": "Élevée", "medium": "Moyenne", "low": "Faible"}

NAV_ITEMS = {
    "Predict": "Inférence",
    "Batch": "Analyse",
    "About": "Moteur",
}

SEASON_OPTIONS = ["printemps", "ete", "automne", "hiver"]
HOUR_OPTIONS = [
    "0h-3h", "3h-6h", "6h-9h", "9h-12h",
    "12h-15h", "15h-18h", "18h-21h", "21h-24h",
]

# =================================================================
# UTILITAIRES UI
# =================================================================
def card_marker() -> None:
    st.markdown('<span class="aurora-card-marker aurora-marker"></span>', unsafe_allow_html=True)


def info_card_marker() -> None:
    st.markdown('<span class="info-card-marker aurora-marker"></span>', unsafe_allow_html=True)


def section_header(tag: str, title_html: str, lead: str) -> None:
    st.markdown(
        f"""
        <div class="section-intro">
            <div class="inference-tag">{tag}</div>
            <div class="main-title">{title_html}</div>
            <p class="lead-text">{lead}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_label(label: str, unit: str) -> None:
    st.markdown(
        f'<div class="input-label-row"><span>{label}</span><span class="unit-tag">{unit}</span></div>',
        unsafe_allow_html=True,
    )


def render_help(help_text: str) -> None:
    st.markdown(f'<div class="sub-help">{help_text}</div>', unsafe_allow_html=True)


def risk_label(prediction_value: int) -> str:
    return "RISQUE ÉLEVÉ" if prediction_value == 1 else "RISQUE FAIBLE"


def render_nav_slot(page_key: str) -> None:
    if st.session_state.page == page_key:
        st.markdown('<div class="nav-slot"><span class="nav-active-label">● actif</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="nav-slot"><span class="nav-slot-spacer">&nbsp;</span></div>', unsafe_allow_html=True)


# =================================================================
# UTILITAIRES MÉTIER
# =================================================================
def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def month_to_cyclical(month: int) -> tuple[float, float]:
    angle = 2 * math.pi * (month - 1) / 12
    return math.sin(angle), math.cos(angle)


def build_storm_features_payload(raw: dict) -> dict:
    """Construit le corps JSON simplifié attendu par POST /predict."""
    return {
        "solar_wind_speed": float(raw["solar_wind_speed"]),
        "solar_wind_density": float(raw["solar_wind_density"]),
        "bz_component": float(raw["bz_component"]),
        "dst_index": float(raw["dst_index"]),
        "month": int(raw.get("month", datetime.now().month)),
        "season": raw["season"],
        "hour_interval": raw["hour_interval"],
        "is_solar_maximum": int(raw["is_solar_maximum"]),
    }


def prepare_batch_for_api(df: pd.DataFrame) -> pd.DataFrame:
    """Aligne le CSV sur les 13 features attendues par POST /predict/batch."""
    df = df.copy()
    if "month" not in df.columns:
        df["month"] = datetime.now().month
    if "sin_month" not in df.columns:
        df["sin_month"] = df["month"].apply(lambda m: month_to_cyclical(int(m))[0])
    if "cos_month" not in df.columns:
        df["cos_month"] = df["month"].apply(lambda m: month_to_cyclical(int(m))[1])
    return df


def parse_api_error(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail", response.text)
        if isinstance(detail, list):
            return "; ".join(str(item) for item in detail)
        return str(detail)
    except Exception:
        return response.text or f"Erreur HTTP {response.status_code}"


def api_health_check() -> dict | None:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def api_predict_single(raw_features: dict) -> dict:
    payload = build_storm_features_payload(raw_features)
    response = requests.post(
        f"{API_BASE_URL}/predict",
        json=payload,
        timeout=API_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(parse_api_error(response))

    data = response.json()
    is_storm = data["prediction"] == "storm"
    return {
        "prediction": 1 if is_storm else 0,
        "probability": float(data["probability"]),
        "threshold": float(data["threshold"]),
        "confidence": CONFIDENCE_FR.get(data["confidence"], data["confidence"]),
        "payload": payload,
    }


def api_predict_batch(df: pd.DataFrame, progress_bar=None) -> pd.DataFrame:
    df_prepared = prepare_batch_for_api(df)
    csv_bytes = df_prepared.to_csv(index=False).encode("utf-8")

    if progress_bar is not None:
        progress_bar.progress(0.25, text="Envoi du fichier à l'API Aurora…")

    response = requests.post(
        f"{API_BASE_URL}/predict/batch",
        files={"file": ("batch.csv", csv_bytes, "text/csv")},
        timeout=API_TIMEOUT,
    )
    if not response.ok:
        raise RuntimeError(parse_api_error(response))

    if progress_bar is not None:
        progress_bar.progress(0.85, text="Réception des résultats…")

    return pd.read_csv(io.BytesIO(response.content))


def confidence_label(probability: float, threshold: float) -> str:
    diff = abs(probability - threshold)
    if diff > 0.30:
        return "Élevée"
    if diff > 0.15:
        return "Moyenne"
    return "Faible"


def risk_label(prediction) -> str:
    if isinstance(prediction, str):
        return "Risque Élevé" if prediction == "storm" else "Risque Faible"
    return "Risque Élevé" if int(prediction) == 1 else "Risque Faible"


# =================================================================
# HEADER
# =================================================================
if "page" not in st.session_state:
    st.session_state.page = "Predict"

header_cols = st.columns([1.3, 3.4, 1.3], gap="small")

with header_cols[0]:
    st.markdown('<span class="header-row-marker aurora-marker"></span>', unsafe_allow_html=True)
    # Calcul du chemin absolu vers la racine du projet à partir de ce fichier
    # (app/ui/app.py -> remonter de 2 niveaux pour atteindre la racine)
    root_path = Path(__file__).parents[2]
    logo_path = root_path / "assets" / "logo.png"
    try:
        logo_base64 = get_base64_image(str(logo_path))
        st.markdown(
            f"""
            <div class="header-logo-container">
                <img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="AURORA">
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown(
            """
            <div class="header-logo-container">
                <div style="font-family: 'Playfair Display', serif; font-size: 1.2rem; color: white;">AURORA</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with header_cols[1]:
    nav_cols = st.columns(3, gap="small")
    for col, (page_key, btn_key) in zip(nav_cols, [("Predict", "nav1"), ("Batch", "nav2"), ("About", "nav3")]):
        with col:
            if st.button(NAV_ITEMS[page_key].upper(), key=btn_key):
                st.session_state.page = page_key
            render_nav_slot(page_key)

with header_cols[2]:
    health = api_health_check()
    if health and health.get("model_loaded"):
        status_dot = "#4fd1c5"
        status_text = "API connectée"
    else:
        status_dot = "#ed64a6"
        status_text = "API hors ligne"
    st.markdown(
        f"""
        <div class="header-status">
            <div class="status-badge">
                <span style="color: {status_dot}; font-size: 0.6rem;">●</span>
                <span style="color: white; font-size: 0.6rem; font-weight: 600;">
                    {status_text} <span style="color: #718096;">v2.4.1</span>
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<hr class="header-divider">', unsafe_allow_html=True)

# =================================================================
# PAGE : INFÉRENCE
# =================================================================
if st.session_state.page == "Predict":
    section_header(
        "Analyse de télémétrie en temps réel",
        'Prédire la <span>danse des aurores</span>',
        "Saisissez les paramètres OMNI2 pour une prédiction via l'API Aurora "
        "(POST /predict) — horizon 6 heures.",
    )

    st.markdown('<span class="predict-grid-marker aurora-marker"></span>', unsafe_allow_html=True)
    col_form, col_res = st.columns([1.35, 1], gap="large")

    with col_form:
        card_marker()
        st.markdown('<div class="card-title">Entrées des Capteurs</div>', unsafe_allow_html=True)

        with st.form("prediction_form"):
            f1, f2 = st.columns(2, gap="medium")

            with f1:
                render_label("Vitesse vent solaire", "km/s")
                sw_speed = st.number_input("sws", 200.0, 1200.0, 391.0, 10.0, label_visibility="collapsed")
                render_help("Typique : 300–800")

                render_label("Densité vent solaire", "p/cm³")
                sw_density = st.number_input("swd", 0.0, 100.0, 4.9, 0.1, label_visibility="collapsed")
                render_help("Densité du plasma interplanétaire")

                render_label("Composante Bz", "nT")
                bz = st.number_input("bz", -50.0, 30.0, -0.2, 0.1, label_visibility="collapsed")
                render_help("Sudward (négatif) = risque de reconnexion")

                render_label("Mois d'observation", "1–12")
                month = st.selectbox(
                    "month",
                    list(range(1, 13)),
                    index=datetime.now().month - 1,
                    format_func=lambda m: f"Mois {m}",
                    label_visibility="collapsed",
                )
                render_help("Le calcul cyclique (sin/cos) est géré automatiquement")

            with f2:
                render_label("Indice Dst", "nT")
                dst = st.number_input("dst", -400.0, 50.0, -6.0, 1.0, label_visibility="collapsed")
                render_help("Intensité de la tempête (Dst < −50 nT)")

                render_label("Maximum solaire", "Cycle")
                solar_max = st.selectbox("smax", [0, 1], format_func=lambda x: "Oui" if x == 1 else "Non", label_visibility="collapsed")
                render_help("Phase de maximum du cycle solaire 25")

                render_label("Saison", "Nominal")
                season = st.selectbox("season", SEASON_OPTIONS, label_visibility="collapsed")
                render_help("Saison météorologique de l'observation")

                render_label("Intervalle horaire", "UTC")
                hour = st.selectbox("hour", HOUR_OPTIONS, label_visibility="collapsed")
                render_help("Créneau horaire de la mesure")

            run_btn = st.form_submit_button("Initier l'inférence")

    with col_res:
        card_marker()
        st.markdown('<div class="card-title">Résultat de l\'Inférence</div>', unsafe_allow_html=True)

        if run_btn:
            input_data = {
                "solar_wind_speed": sw_speed,
                "solar_wind_density": sw_density,
                "bz_component": bz,
                "dst_index": dst,
                "month": month,
                "is_solar_maximum": solar_max,
                "season": season,
                "hour_interval": hour,
            }

            try:
                with st.spinner("Appel API Aurora en cours…"):
                    result = api_predict_single(input_data)

                status_class = "status-high" if result["prediction"] == 1 else "status-low"
                status_text = risk_label(result["prediction"])
                narrative = (
                    "Une perturbation géomagnétique majeure est probable. Aurores visibles possibles aux hautes latitudes."
                    if result["prediction"] == 1
                    else "Conditions magnétosphériques stables. Aucune tempête majeure attendue sur l'horizon de 6 h."
                )

                st.markdown(
                    f"""
                    <div class="result-panel">
                        <div class="prob-val">{result['probability'] * 100:.1f}%</div>
                        <div class="result-status">{status_text}</div>
                        <div class="status-pill {status_class}">Confiance {result['confidence'].lower()}</div>
                        <div class="result-meta">
                            <b>Seuil de décision :</b> {result['threshold']}<br><br>
                            {narrative}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception as exc:
                st.error(f"Échec de l'appel API ({API_BASE_URL}/predict) : {exc}")
        else:
            st.markdown(
                """
                <div class="empty-state">
                    <div style="font-size: 4rem; margin-bottom: 1.5rem; opacity: 0.5;">✨</div>
                    <div style="color: white; font-family: 'Playfair Display', serif; font-size: 1.5rem; margin-bottom: 0.75rem;">
                        En attente de données
                    </div>
                    <div style="color: #718096; font-size: 0.9rem; max-width: 300px; line-height: 1.6;">
                        Complétez les entrées des capteurs puis lancez l'inférence neuronale.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =================================================================
# PAGE : ANALYSE COLLECTIVE
# =================================================================
elif st.session_state.page == "Batch":
    section_header(
        "Traitement de données collectives",
        'Analyse par <span>lot</span>',
        "Importez un fichier CSV OMNI2 pour traiter plusieurs observations "
        "et obtenir les probabilités de tempête en série.",
    )

    batch_col, = st.columns(1)
    with batch_col:
        card_marker()
        st.markdown('<div class="card-title">Import & Traitement</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="upload-intro">
                Colonnes minimales (POST /predict/batch) :<br>
                <code>{", ".join(REQUIRED_BATCH_COLUMNS)}</code><br>
                <span style="font-size:0.82rem;">month, sin_month, cos_month ajoutés automatiquement si absents.</span>
            </div>
            <div class="upload-zone-header">
                <div class="icon">☁️</div>
                <div class="title">Zone de dépôt CSV</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<span class="upload-panel-marker aurora-marker"></span>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Choisir un fichier CSV", type="csv", label_visibility="collapsed", key="batch_uploader",
        )
        st.markdown('<div class="upload-hint">Taille max. 10 Mo · Encodage UTF-8 recommandé</div>', unsafe_allow_html=True)

        if uploaded_file is not None:
            df_batch = pd.read_csv(uploaded_file)
            missing_cols = [c for c in REQUIRED_BATCH_COLUMNS if c not in df_batch.columns]

            if missing_cols:
                st.error(
                    f"Colonnes manquantes : {', '.join(missing_cols)}. "
                    "Veuillez fournir un CSV conforme au schéma OMNI2."
                )
            else:
                st.markdown('<div class="card-title-sm">Aperçu — 5 premières lignes</div>', unsafe_allow_html=True)
                st.dataframe(df_batch.head(5), use_container_width=True, hide_index=True)

                if st.button("Lancer l'analyse du lot", key="batch_run"):
                    progress = st.progress(0.0, text="Initialisation du pipeline d'inférence…")
                    try:
                        with st.spinner("Traitement via l'API Aurora…"):
                            df_results = api_predict_batch(df_batch, progress_bar=progress)
                            progress.progress(1.0, text="Analyse terminée")

                        threshold = float(df_results["threshold"].iloc[0]) if "threshold" in df_results.columns else 0.28
                        df_results["probabilité_%"] = df_results["probability"].map(lambda p: f"{float(p):.1%}")
                        df_results["résultat"] = df_results["prediction"].map(risk_label)
                        df_results["confiance"] = df_results["probability"].map(
                            lambda p: confidence_label(float(p), threshold)
                        )
                        st.session_state.batch_results = df_results
                        st.session_state.batch_done = True
                    except Exception as exc:
                        st.error(f"Échec de l'appel API ({API_BASE_URL}/predict/batch) : {exc}")

                if st.session_state.get("batch_done"):
                    st.markdown('<div class="card-title-sm">Résultats enrichis</div>', unsafe_allow_html=True)
                    display_df = st.session_state.batch_results.copy()
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "probabilité_%": st.column_config.TextColumn("Probabilité", width="small"),
                            "résultat": st.column_config.TextColumn("Verdict", width="medium"),
                            "confiance": st.column_config.TextColumn("Confiance", width="small"),
                            "bz_component": st.column_config.NumberColumn("Bz", format="%.1f nT"),
                            "dst_index": st.column_config.NumberColumn("Dst", format="%.0f nT"),
                        },
                    )
                    csv_export = st.session_state.batch_results.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Télécharger les résultats",
                        data=csv_export,
                        file_name=f"aurora_batch_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="download_batch",
                    )

# =================================================================
# PAGE : MOTEUR AURORA
# =================================================================
elif st.session_state.page == "About":
    section_header(
        "Spécifications techniques",
        'Le moteur <span>Aurora</span>',
        "Architecture, données et performances du modèle de prédiction "
        "des tempêtes géomagnétiques à horizon 6 heures.",
    )

    st.markdown('<span class="about-info-grid-marker aurora-marker"></span>', unsafe_allow_html=True)
    info_cols = st.columns(3, gap="medium")
    info_cards = [
        (
            "Intelligence API",
            "Contrairement aux versions précédentes, l'<b>API Aurora v2</b> est désormais 'intelligente'. "
            "Elle calcule automatiquement les features physiques (pression, bz_negative) "
            "et temporelles (sin/cos month, interactions) à partir des données brutes. "
            "Cela simplifie l'intégration pour n'importe quel système tiers.",
        ),
        (
            "Algorithme",
            "Le modèle utilise un <b>Random Forest</b> optimisé. La stratégie de "
            "<b>sous-échantillonnage (Undersampling)</b> a été choisie pour traiter le "
            "déséquilibre naturel des tempêtes (8,5%). Le seuil de décision est calibré "
            "à <b>0,28</b> pour garantir une détection maximale des risques.",
        ),
        (
            "Priorité Métier",
            "Le système privilégie le <b>Rappel (Recall > 90%)</b>. L'objectif est de "
            "ne manquer aucune tempête pour protéger les réseaux électriques et satellites, "
            "quitte à accepter un taux de faux positifs plus élevé pour une sécurité maximale.",
        ),
    ]

    for col, (title, body) in zip(info_cols, info_cards):
        with col:
            info_card_marker()
            st.markdown(f'<div class="info-mini-card"><h4>{title}</h4><p>{body}</p></div>', unsafe_allow_html=True)

    st.markdown('<div style="height: 1.75rem;"></div>', unsafe_allow_html=True)

    st.markdown('<span class="about-metrics-grid-marker aurora-marker"></span>', unsafe_allow_html=True)
    metrics_col, model_col = st.columns([1.2, 1], gap="large")

    with metrics_col:
        card_marker()
        st.markdown('<div class="card-title">Métriques de validation</div>', unsafe_allow_html=True)
        m1, m2 = st.columns(2, gap="medium")
        metrics = [
            ("Recall (Sensibilité)", "92.2%"),
            ("ROC AUC", "0.955"),
            ("F1 Score", "0.526"),
            ("Précision", "36.9%"),
        ]
        for i, (title, value) in enumerate(metrics):
            with (m1 if i % 2 == 0 else m2):
                st.markdown(
                    f'<div class="metric-grid-item"><div class="metric-title">{title}</div>'
                    f'<div class="metric-val">{value}</div></div>',
                    unsafe_allow_html=True,
                )

    with model_col:
        card_marker()
        st.markdown('<div class="card-title">Fiche modèle</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="model-desc">
                Aurora classe chaque observation en <b>Risque Élevé</b> ou <b>Risque Faible</b>
                en analysant l'interaction entre le vent solaire et la magnétosphère terrestre.
                Le modèle est entraîné sur 5 ans de données horaires (2019–2023).
            </div>
            <div class="model-footer-card">
                <div class="model-footer-row">
                    <span class="model-footer-label">Version</span>
                    <span class="model-footer-value">v2.4.1</span>
                </div>
                <div class="model-footer-row">
                    <span class="model-footer-label">Jeu de données</span>
                    <span class="model-footer-value">NASA OMNI2</span>
                </div>
                <div class="model-footer-row">
                    <span class="model-footer-label">Algorithme</span>
                    <span class="model-footer-value">Random Forest + Undersampling</span>
                </div>
                <div class="model-footer-row">
                    <span class="model-footer-label">Statut</span>
                    <span class="model-footer-status">Opérationnel</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =================================================================
# FOOTER
# =================================================================
st.markdown(
    f'<div class="page-footer">AURORA SYSTEM · SPACE WEATHER ANALYTICS · {datetime.now().year}</div>',
    unsafe_allow_html=True,
)
