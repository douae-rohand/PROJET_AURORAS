import joblib
import pandas as pd
from app.api.logger import logger

# ============================================================
# Chargement unique au démarrage + Métadonnées depuis le fichier
# ============================================================
MODEL_PATH = "models/final_model.joblib"

try:
    data = joblib.load(MODEL_PATH)
    model = data["pipeline"] if isinstance(data, dict) else data

    # Lecture des vraies valeurs depuis le dictionnaire sauvegardé
    THRESHOLD = data["decision_threshold"]   # 0.28

    MODEL_METADATA = {
        "model_type"   : data["model_name"],
        "strategy"     : data["strategy"],
        "version"      : "1.0",
        "training_date": "2026-05-13",
        "target"       : "is_storm",
        "threshold"    : THRESHOLD,
        "best_params"  : data["best_params"],
        "performance"  : {
            "recall_cv"             : data["recall_cv"],
            "recall_test_optimal"   : data["recall_test_optimal_threshold"],
            "recall_test_default"   : data["recall_test_default_threshold"],
            "pr_auc_test"           : data["pr_auc_test"]
        },
        "features": [
            "solar_wind_speed", "solar_wind_density", "bz_component",
            "solar_wind_pressure", "bz_min_3h", "dst_index",
            "month", "sin_month", "cos_month", "season",
            "hour_interval", "bz_negative", "is_solar_maximum"
        ]
    }
    logger.info(f"Modèle '{MODEL_METADATA['model_type']}' chargé (seuil={THRESHOLD})")

except Exception as e:
    logger.error(f"ERREUR de chargement du modèle : {e}")
    model = None
    THRESHOLD = 0.28
    MODEL_METADATA = {}


# ============================================================
# Feature Engineering on the fly
# ============================================================
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recrée le feature engineering complet à la volée :
      - Pression solaire (physique)
      - Encodage cyclique du mois
      - Signe de Bz (bz_negative)
      - Interaction bz × dst
      - Variables de fenêtre (bz_min_3h, dst_rate_change)
      - One-Hot Encoding (season, hour_interval)
    """
    df = df.copy()

    # 1. Features physiques de base
    if "solar_wind_density" in df.columns and "solar_wind_speed" in df.columns:
        df["solar_wind_pressure"] = df["solar_wind_density"] * (df["solar_wind_speed"]**2)

    if "bz_component" in df.columns:
        df["bz_negative"] = (df["bz_component"] < 0).astype(int)
        # En prédiction unitaire, on ne connaît pas le passé, donc min_3h = bz actuel
        if "bz_min_3h" not in df.columns:
            df["bz_min_3h"] = df["bz_component"]

    # 2. Encodage cyclique du mois
    if "month" in df.columns:
        import numpy as np
        df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
        df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)

    # 3. Feature d'interaction bz × dst
    if "bz_component" in df.columns and "dst_index" in df.columns:
        df["bz_dst_interaction"] = df["bz_component"] * df["dst_index"]

    # 2. dst_rate_change nécessite 2 points temporels consécutifs.
    #    En prédiction unitaire, on fixe à 0 (valeur neutre / pas de variation).
    df["dst_rate_change"] = 0.0

    # 3. One-Hot Encoding de la saison
    for s in ["hiver", "printemps", "ete", "automne"]:
        if "season" in df.columns:
            df[f"season_{s}"] = (df["season"] == s).astype(int)

    # 4. One-Hot Encoding de l'intervalle horaire
    #    L'API accepte le format "06-09" (lisible), le modèle attend "6h-9h"
    intervals_map = {
        "00-03": "0h-3h",   "03-06": "3h-6h",   "06-09": "6h-9h",   "09-12": "9h-12h",
        "12-15": "12h-15h", "15-18": "15h-18h", "18-21": "18h-21h", "21-24": "21h-24h",
        "0h-3h": "0h-3h",   "3h-6h": "3h-6h",   "6h-9h": "6h-9h",   "9h-12h": "9h-12h",
        "12h-15h": "12h-15h", "15h-18h": "15h-18h", "18h-21h": "18h-21h", "21h-24h": "21h-24h"
    }
    if "hour_interval" in df.columns:
        df["mapped"] = df["hour_interval"].map(intervals_map)
        for i in ["0h-3h", "3h-6h", "6h-9h", "9h-12h", "12h-15h", "15h-18h", "18h-21h", "21h-24h"]:
            df[f"hour_interval_{i}"] = (df["mapped"] == i).astype(int)
        df = df.drop(columns=["mapped"])

    # 5. Suppression des colonnes sources (remplacées par leur encodage)
    cols_to_drop = [c for c in ["season", "hour_interval", "month"] if c in df.columns]
    df = df.drop(columns=cols_to_drop)

    # 6. Forcer l'ordre exact et la présence des 24 colonnes attendues par le ColumnTransformer
    expected_cols = [
        'solar_wind_speed', 'solar_wind_density', 'bz_component', 'solar_wind_pressure', 'bz_min_3h',
        'dst_index', 'bz_dst_interaction', 'dst_rate_change', 'sin_month', 'cos_month', 'bz_negative',
        'is_solar_maximum', 'season_automne', 'season_ete', 'season_hiver', 'season_printemps',
        'hour_interval_0h-3h', 'hour_interval_3h-6h', 'hour_interval_6h-9h', 'hour_interval_9h-12h',
        'hour_interval_12h-15h', 'hour_interval_15h-18h', 'hour_interval_18h-21h', 'hour_interval_21h-24h'
    ]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = 0.0

    return df[expected_cols]


# ============================================================
# Prédictions
# ============================================================
def predict_single(features: dict) -> dict:
    if model is None:
        raise RuntimeError("Modèle non chargé, impossible de prédire.")

    df_raw = pd.DataFrame([features])
    df_eng = engineer_features(df_raw)
    proba = model.predict_proba(df_eng)[0][1]

    prediction = int(proba >= THRESHOLD)
    label      = "storm" if prediction == 1 else "calm"

    distance = abs(proba - THRESHOLD)
    if distance >= 0.3:   confidence = "high"
    elif distance >= 0.15: confidence = "medium"
    else:                  confidence = "low"

    logger.info(f"Prediction unitaire: {label} (proba={proba:.3f})")

    return {
        "prediction" : label,
        "probability": round(float(proba), 4),
        "threshold"  : THRESHOLD,
        "confidence" : confidence
    }


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    if model is None:
        raise RuntimeError("Modèle non chargé, impossible de prédire.")

    df_eng = engineer_features(df)
    probas = model.predict_proba(df_eng)[:, 1]

    predictions = (probas >= THRESHOLD).astype(int)
    labels      = ["storm" if p == 1 else "calm" for p in predictions]

    df_result = df.copy()
    df_result["prediction"]  = labels
    df_result["probability"] = probas.round(4)
    df_result["threshold"]   = THRESHOLD

    logger.info(f"Prediction batch: {len(df_result)} lignes traitees")
    return df_result
