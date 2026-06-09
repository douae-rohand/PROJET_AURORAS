import streamlit as st
import pandas as pd
import numpy as np
import time
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
        background: radial-gradient(circle at top right, #1a0b2e, #050505) !important;
        font-family: 'Inter', sans-serif !important;
        color: #e2e8f0 !important;
    }

    .main .block-container {
        padding-top: 0.75rem !important;
        padding-left: 6% !important;
        padding-right: 6% !important;
        max-width: 100% !important;
    }

    [data-testid="stHeader"] { background: rgba(0,0,0,0); height: 0; }

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
    .predict-grid-marker,
    .about-info-grid-marker,
    .about-metrics-grid-marker {
        display: none !important;
    }

    /* Panneaux glassmorphism — appliqués sur la colonne Streamlit */
    div[data-testid="column"]:has(.aurora-card-marker) > div[data-testid="stVerticalBlock"] {
        background: rgba(15, 15, 35, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.5rem 2rem;
        box-shadow: 0 20px 50px rgba(0,0,0,0.6);
        height: 100%;
    }

    div[data-testid="column"]:has(.info-card-marker) > div[data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
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

    /* Header — une seule ligne */
    .header-logo-container {
        display: flex;
        align-items: center;
        padding: 0;
        margin-left: -35px;
        margin-top: -6px;
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
        padding-top: 8px;
    }

    .status-badge {
        background: rgba(79, 209, 197, 0.1);
        border-radius: 20px;
        padding: 4px 12px;
        border: 1px solid rgba(79, 209, 197, 0.3);
        white-space: nowrap;
    }

    /* Navigation */
    .stButton > button[key^="nav"] {
        background: linear-gradient(135deg, #6b46c1 0%, #4fd1c5 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 6px 14px !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        box-shadow: 0 0 15px rgba(128, 90, 213, 0.3) !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
        width: 100% !important;
        min-width: 0 !important;
    }

    .stButton > button[key^="nav"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(79, 209, 197, 0.5) !important;
    }

    .header-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin: 0.25rem 0 2rem 0;
    }

    /* Sections */
    .section-intro {
        margin-bottom: 3rem;
    }

    .card-title {
        color: white;
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        margin-bottom: 1.75rem;
        margin-top: 0;
    }

    .card-title-sm {
        color: white;
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
        color: white;
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
        color: #a0aec0;
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
        color: #cbd5e0;
        font-size: 0.98rem;
        line-height: 1.75;
        font-weight: 300;
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
        color: #a0aec0;
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
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
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
        color: #a0aec0 !important;
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
        color: white;
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        margin-bottom: 0.75rem;
    }

    .result-meta {
        color: #a0aec0;
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
        color: white;
        font-family: 'Playfair Display', serif;
        font-size: 1.35rem;
    }

    div[data-testid="column"]:has(.upload-panel-marker) [data-testid="stFileUploader"] {
        margin-top: 0 !important;
    }

    div[data-testid="column"]:has(.upload-panel-marker) [data-testid="stFileUploader"] section {
        background: rgba(0, 0, 0, 0.2) !important;
        border: 1px dashed rgba(79, 209, 197, 0.35) !important;
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
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
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
        color: white;
        font-weight: 700;
        font-family: 'Playfair Display', serif;
    }

    .model-desc {
        color: #cbd5e0;
        font-size: 1rem;
        line-height: 1.8;
        margin-bottom: 1.5rem;
    }

    .model-footer-card {
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .model-footer-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.85rem;
        font-size: 0.9rem;
    }

    .model-footer-label { color: #718096; }
    .model-footer-value { color: white; font-weight: 600; }
    .model-footer-status { color: #4fd1c5; font-weight: 600; }

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
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
# CONSTANTES
# =================================================================
PREDICTION_THRESHOLD = 0.28

REQUIRED_BATCH_COLUMNS = [
    "solar_wind_speed",
    "solar_wind_density",
    "bz_component",
    "solar_wind_pressure",
    "bz_min_3h",
    "dst_index",
    "dst_rate_change",
    "bz_negative",
    "is_solar_maximum",
    "season",
    "hour_interval",
]

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


def nav_button_label(page_key: str) -> str:
    name = NAV_ITEMS[page_key].upper()
    if st.session_state.page == page_key:
        return f"● {name}"
    return name


# =================================================================
# UTILITAIRES MÉTIER
# =================================================================
def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def month_to_cyclical(month: int) -> tuple[float, float]:
    angle = 2 * math.pi * (month - 1) / 12
    return math.sin(angle), math.cos(angle)


def enrich_payload(raw: dict) -> dict:
    payload = raw.copy()
    payload["bz_dst_interaction"] = payload["bz_component"] * payload["dst_index"]
    sin_month, cos_month = month_to_cyclical(int(payload.get("month", datetime.now().month)))
    payload["sin_month"] = sin_month
    payload["cos_month"] = cos_month
    return payload


def compute_storm_score(row: dict | pd.Series) -> float:
    bz = float(row["bz_component"])
    dst = float(row["dst_index"])
    sws = float(row.get("solar_wind_speed", 400))
    dst_rate = float(row.get("dst_rate_change", 0))
    bz_min = float(row.get("bz_min_3h", bz))

    score = 0.05
    if bz < -5:
        score += 0.30
    if bz < -10:
        score += 0.10
    if dst < -30:
        score += 0.15
    if dst < -50:
        score += 0.25
    if dst < -100:
        score += 0.10
    if sws > 500:
        score += 0.08
    if sws > 700:
        score += 0.05
    if bz_min < -10:
        score += 0.07
    if dst_rate < -20:
        score += 0.08
    if bz * dst > 100:
        score += 0.06
    if int(row.get("bz_negative", 0)) == 1 and dst < -20:
        score += 0.05
    return score


def confidence_label(probability: float, threshold: float = PREDICTION_THRESHOLD) -> str:
    diff = abs(probability - threshold)
    if diff > 0.30:
        return "Élevée"
    if diff > 0.15:
        return "Moyenne"
    return "Faible"


def risk_label(prediction: int) -> str:
    return "Risque Élevé" if prediction == 1 else "Risque Faible"


def mock_api_call(data, progress_bar=None):
    """
    Simule un appel à l'API FastAPI Aurora.
    # TODO: replace with requests.post("http://localhost:8000/predict", json=payload)
    # TODO: replace with requests.post("http://localhost:8000/predict/batch", files=...)
    """
    time.sleep(0.6)

    if isinstance(data, pd.DataFrame):
        probas = []
        total = len(data)
        for idx, (_, row) in enumerate(data.iterrows()):
            score = compute_storm_score(row)
            prob = min(0.99, max(0.01, score + np.random.normal(0, 0.04)))
            probas.append(prob)
            if progress_bar is not None and total > 0:
                progress_bar.progress(min(1.0, (idx + 1) / total))

        predictions = [1 if p >= PREDICTION_THRESHOLD else 0 for p in probas]
        return {
            "predictions": predictions,
            "probabilities": probas,
            "threshold": PREDICTION_THRESHOLD,
        }

    payload = enrich_payload(data)
    score = compute_storm_score(payload)
    probability = min(0.99, max(0.01, score + np.random.normal(0, 0.04)))
    prediction = 1 if probability >= PREDICTION_THRESHOLD else 0

    return {
        "prediction": prediction,
        "probability": probability,
        "threshold": PREDICTION_THRESHOLD,
        "confidence": confidence_label(probability),
        "payload": payload,
    }


# =================================================================
# HEADER
# =================================================================
if "page" not in st.session_state:
    st.session_state.page = "Predict"

# Logo | 3 onglets adjacents | badge — une ligne, sans colonnes vides
header_cols = st.columns([2.2, 0.9, 0.9, 0.9, 2.2], gap="small")

with header_cols[0]:
    logo_path = Path("assets/logo.png")
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

for col, (page_key, btn_key) in zip(
    header_cols[1:4],
    [("Predict", "nav1"), ("Batch", "nav2"), ("About", "nav3")],
):
    with col:
        if st.button(nav_button_label(page_key), key=btn_key):
            st.session_state.page = page_key

with header_cols[4]:
    st.markdown(
        """
        <div class="header-status">
            <div class="status-badge">
                <span style="color: #4fd1c5; font-size: 0.6rem;">●</span>
                <span style="color: white; font-size: 0.6rem; font-weight: 600;">
                    Modèle <span style="color: #718096;">v2.4.1</span>
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
        "Saisissez les 11 paramètres scientifiques OMNI2 pour estimer la probabilité "
        "d'une tempête géomagnétique dans les 6 prochaines heures.",
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
                sw_speed = st.number_input("sws", 200.0, 2000.0, 391.0, 10.0, label_visibility="collapsed")
                render_help("Typique : 300–800")

                render_label("Densité vent solaire", "p/cm³")
                sw_density = st.number_input("swd", 0.0, 200.0, 4.9, 0.1, label_visibility="collapsed")
                render_help("Densité du plasma interplanétaire")

                render_label("Composante Bz", "nT")
                bz = st.number_input("bz", -100.0, 100.0, -0.2, 0.1, label_visibility="collapsed")
                render_help("Sudward (négatif) = risque de reconnexion")

                render_label("Pression dynamique", "nPa")
                sw_pressure = st.number_input("swp", 0.0, 20000000.0, 787989.0, 1000.0, label_visibility="collapsed")
                render_help("Pression du vent solaire")

                render_label("Bz minimum (3 h)", "nT")
                bz_min_3h = st.number_input("bzmin", -100.0, 100.0, -1.2, 0.1, label_visibility="collapsed")
                render_help("Minimum glissant sur 3 heures")

                render_label("Variation Dst (3 h)", "nT/3h")
                dst_rate = st.number_input("dstr", -500.0, 500.0, 0.0, 1.0, label_visibility="collapsed")
                render_help("Vitesse de dégradation magnétique")

            with f2:
                render_label("Indice Dst", "nT")
                dst = st.number_input("dst", -600.0, 100.0, -6.0, 1.0, label_visibility="collapsed")
                render_help("Intensité de la tempête (Dst < −50 nT)")

                render_label("Bz négatif", "Binaire")
                bz_neg = st.selectbox("bzn", [0, 1], format_func=lambda x: "Oui" if x == 1 else "Non", label_visibility="collapsed")
                render_help("Reconnexion magnétique active")

                render_label("Maximum solaire", "Cycle")
                solar_max = st.selectbox("smax", [0, 1], format_func=lambda x: "Oui" if x == 1 else "Non", label_visibility="collapsed")
                render_help("Phase de maximum du cycle solaire")

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
                "solar_wind_pressure": sw_pressure,
                "bz_min_3h": bz_min_3h,
                "dst_index": dst,
                "dst_rate_change": dst_rate,
                "bz_negative": bz_neg,
                "is_solar_maximum": solar_max,
                "season": season,
                "hour_interval": hour,
            }

            with st.spinner("Analyse des motifs spectraux en cours…"):
                result = mock_api_call(input_data)

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
                        <b>Seuil de décision :</b> {result['threshold']}<br>
                        <b>Interaction Bz×Dst :</b> {result['payload']['bz_dst_interaction']:.1f} nT²<br><br>
                        {narrative}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
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
                Colonnes attendues (11 features) :<br>
                <code>{", ".join(REQUIRED_BATCH_COLUMNS)}</code>
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
                    with st.spinner("Traitement de la télémétrie collective…"):
                        if "bz_dst_interaction" not in df_batch.columns:
                            df_batch = df_batch.copy()
                            df_batch["bz_dst_interaction"] = df_batch["bz_component"] * df_batch["dst_index"]
                        results = mock_api_call(df_batch, progress_bar=progress)
                        progress.progress(1.0, text="Analyse terminée")

                    df_results = df_batch.copy()
                    df_results["probabilité"] = results["probabilities"]
                    df_results["probabilité_%"] = df_results["probabilité"].map(lambda p: f"{p:.1%}")
                    df_results["résultat"] = [risk_label(r) for r in results["predictions"]]
                    df_results["confiance"] = df_results["probabilité"].map(confidence_label)
                    st.session_state.batch_results = df_results
                    st.session_state.batch_done = True

                if st.session_state.get("batch_done"):
                    st.markdown('<div class="card-title-sm">Résultats enrichis</div>', unsafe_allow_html=True)
                    display_df = st.session_state.batch_results[
                        [c for c in st.session_state.batch_results.columns if c != "probabilité"]
                    ]
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
            "Architecture",
            "Le cœur du système repose sur une <b>Forêt Aléatoire (Random Forest)</b> "
            "combinée à une stratégie de <b>sous-échantillonnage (Undersampling)</b> "
            "pour compenser le fort déséquilibre des classes (~8,5 % de tempêtes). "
            "Le seuil de décision optimal est fixé à <b>0,28</b> pour maximiser le rappel.",
        ),
        (
            "Données",
            "Les features proviennent du jeu <b>NASA OMNI2</b> (vent solaire au point L1) "
            "et la cible des événements officiels <b>NASA DONKI</b>. "
            "Onze paramètres scientifiques alimentent le pipeline, enrichis par des "
            "features d'interaction (<code>bz_dst_interaction</code>) et temporelles "
            "(<code>dst_rate_change</code>, encodage cyclique du mois).",
        ),
        (
            "Limites connues",
            "<b>Faux positifs :</b> le modèle privilégie le rappel (92,2 %), ce qui peut "
            "générer des alertes sur des événements mineurs.<br><br>"
            "<b>Dépendance capteurs :</b> la qualité dépend des satellites DSCOVR/ACE.<br><br>"
            "<b>Horizon :</b> prédiction limitée à 6 heures, sans capacité de prévision à long terme.",
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
