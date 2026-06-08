import joblib
import numpy as np
import pandas as pd
from app.logger import logger

MODEL_PATH = "models/final_model.joblib"
THRESHOLD  = 0.28

MODEL_METADATA = {
    "model_type"      : "Random Forest + Undersampling",
    "version"         : "1.0",
    "training_date"   : "2026-05-13", # N'hésite pas à ajuster la date
    "target"          : "is_storm",
    "threshold"       : THRESHOLD,
    "performance": {
        "recall"    : 0.9145,
        "f1_score"  : 0.5238,
        "precision" : 0.3670,
        "roc_auc"   : 0.9546
    },
    "features": [
        "solar_wind_speed", "solar_wind_density", "bz_component",
        "solar_wind_pressure", "bz_min_3h", "dst_index",
        "month", "sin_month", "cos_month", "season",
        "hour_interval", "bz_negative", "is_solar_maximum"
    ]
}

# ============================================================
# Chargement unique au démarrage
# ============================================================
try:
    # L'API essaie de charger l'objet (qui s'avère être un dictionnaire de la Phase 3)
    data = joblib.load(MODEL_PATH)
    # On extrait le véritable algorithme (le pipeline) !
    model = data["pipeline"]
    logger.info(f"Modèle chargé avec succès depuis {MODEL_PATH}")
except FileNotFoundError:
    # Si le fichier est introuvable, l'API ne crashe pas brutalement au démarrage,
    # elle loggue l'erreur pour t'aider à débugger.
    logger.error(f"ERREUR : fichier modèle introuvable à {MODEL_PATH}")
    model = None


def predict_single(features: dict) -> dict:
    """
    Prédit pour un seul cas (une seule ligne).
    Retourne la prédiction, la probabilité, le seuil, et un niveau de confiance.
    """
    if model is None:
        raise RuntimeError("Modèle non chargé, impossible de prédire.")

    # Convertit les features reçues (dict) en DataFrame d'une ligne
    df = pd.DataFrame([features])
    
    # model.predict_proba retourne [[proba_calm, proba_storm]]. On garde l'indice 1.
    proba = model.predict_proba(df)[0][1]

    # Application du seuil métier au lieu du 0.5 par défaut de Random Forest !
    prediction = int(proba >= THRESHOLD)
    label      = "storm" if prediction == 1 else "calm"

    # Optionnel mais utile pour l'utilisateur de l'API : un niveau de confiance simple
    distance = abs(proba - THRESHOLD)
    if distance >= 0.3:
        confidence = "high"
    elif distance >= 0.15:
        confidence = "medium"
    else:
        confidence = "low"

    logger.info(f"Prédiction unitaire → {label} (proba={proba:.3f})")

    return {
        "prediction" : label,
        "probability": round(float(proba), 4),
        "threshold"  : THRESHOLD,
        "confidence" : confidence
    }


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prédit pour un DataFrame entier avec de multiples lignes (mode batch).
    Retourne le DataFrame enrichi.
    """
    if model is None:
        raise RuntimeError("Modèle non chargé, impossible de prédire.")

    # Calcule les probabilités pour toutes les lignes d'un coup (calcul matriciel optimal)
    probas      = model.predict_proba(df)[:, 1]
    predictions = (probas >= THRESHOLD).astype(int)
    labels      = ["storm" if p == 1 else "calm" for p in predictions]

    df_result = df.copy()
    df_result["prediction"]  = labels
    df_result["probability"] = probas.round(4)
    df_result["threshold"]   = THRESHOLD

    logger.info(f"Prédiction batch → {len(df_result)} lignes traitées")
    return df_result
