"""
OMNI_HAPI.py — Collecte Unifiée via NASA HAPI (Full Parameters)
===============================================================
Ce script télécharge les données horaires depuis NASA OMNI2_H0_MRG1HR.
Stratégie de contournement : On demande TOUTES les colonnes (sans spécifier de paramètres)
pour éviter les bugs de subsetting de l'API NASA, puis on filtre par index.
"""

import os
import time
import logging
import requests
import pandas as pd
import numpy as np
from io import StringIO

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

YEARS = [2019, 2020, 2021, 2022, 2023]
RAW_DIR  = "data/raw"
DATA_DIR = "data"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

HAPI_BASE = "https://cdaweb.gsfc.nasa.gov/hapi"
HAPI_DATASET = "OMNI2_H0_MRG1HR"
FILL_VALUES = [999.9, 9999.0, 9999.99, 99999.0, 99999.99, 9999999.0, -1.0e31, 99, 999]

# -------------------------------------------------
# 1. COLLECTE DES DONNÉES (RAW CSV)
# -------------------------------------------------

def is_fill_value(val) -> bool:
    if val is None or pd.isna(val):
        return True
    for fv in FILL_VALUES:
        if isinstance(val, (int, float)) and abs(val - fv) < 0.1:
            return True
    return False

def fetch_omni_month(year: int, month: int) -> pd.DataFrame:
    """Récupère un mois de données (Toutes les 55 colonnes) au format CSV."""
    start_str = f"{year}-{month:02d}-01T00:00:00Z"
    if month == 12:
        end_str = f"{year+1}-01-01T00:00:00Z"
    else:
        end_str = f"{year}-{month+1:02d}-01T00:00:00Z"

    cache_file = os.path.join(RAW_DIR, f"omni2_hapi_{year}_{month:02d}.csv")

    if os.path.exists(cache_file):
        return pd.read_csv(cache_file, parse_dates=["timestamp"])

    url = f"{HAPI_BASE}/data"
    params = {
        "id": HAPI_DATASET,
        # ON NE MET PLUS 'parameters' -> HAPI va renvoyer les 55 colonnes
        "time.min": start_str,
        "time.max": end_str,
        "format": "csv"
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            
            if "status" in response.text and "1411" in response.text:
                log.error(f"[{year}-{month:02d}] La NASA refuse la requête (Erreur 1411).")
                return pd.DataFrame()
            
            # Application EXACTE de votre logique de filtrage
            lines = [l for l in response.text.split('\n') if not l.startswith('#')]
            if not lines or not lines[0].strip():
                return pd.DataFrame()
                
            df = pd.read_csv(StringIO('\n'.join(lines)), header=None)
            
            cols_utiles = {
                0: 'timestamp', 
                14: 'bz_component', 
                21: 'solar_wind_density', 
                22: 'solar_wind_speed', 
                26: 'solar_wind_pressure',
                46: 'kp_index', 
                47: 'dst_index', 
                49: 'ap_index'
            }
            
            # Garder seulement les colonnes utiles
            df = df[list(cols_utiles.keys())].rename(columns=cols_utiles)
                
            # Nettoyage des fill values de la NASA
            for col in df.columns:
                if col != "timestamp":
                    df[col] = df[col].apply(lambda x: np.nan if is_fill_value(x) else x)
                
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
            
            # Sauvegarde dans le cache
            df.to_csv(cache_file, index=False)
            log.info(f"[{year}-{month:02d}] Téléchargement réussi ({len(df)} lignes).")
            return df
            
        except requests.exceptions.RequestException as e:
            log.warning(f"[{year}-{month:02d}] Erreur réseau (tentative {attempt+1}/{max_retries}) : {e}")
            time.sleep(5 * (attempt + 1))
            
    return pd.DataFrame()

def collect_all_years(years: list) -> pd.DataFrame:
    frames = []
    for y in years:
        log.info(f"--- Collecte de l'année {y} par mois ---")
        year_frames = []
        for m in range(1, 13):
            df = fetch_omni_month(y, m)
            if not df.empty:
                year_frames.append(df)
            time.sleep(30) # Rate limit entre les mois pour laisser respirer le serveur NASA
            
        if year_frames:
            df_year = pd.concat(year_frames)
            frames.append(df_year)
            log.info(f"✅ Année {y} complète : {len(df_year)} lignes.")
            
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).sort_values("timestamp").reset_index(drop=True)

# -------------------------------------------------
# 2. FEATURE ENGINEERING
# -------------------------------------------------

def get_season(m: int) -> str:
    if m in [12, 1, 2]: return "hiver"
    if m in [3, 4, 5]:  return "printemps"
    if m in [6, 7, 8]:  return "ete"
    return "automne"

def get_hour_interval(h: int) -> str:
    start_h = (h // 3) * 3
    return f"{start_h:02d}h-{start_h+3:02d}h"

def apply_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    log.info("Application du Feature Engineering...")

    df["month"] = df["timestamp"].dt.month
    df["season"] = df["month"].apply(get_season)
    df["hour_interval"] = df["timestamp"].dt.hour.apply(get_hour_interval)

    # Cycle Solaire (Phase du cycle 25)
    solar_max_years = {2022, 2023, 2024}
    df["is_solar_maximum"] = df["timestamp"].dt.year.apply(lambda y: 1 if y in solar_max_years else 0)

    # Lags
    df["kp_previous_interval"] = df["kp_index"].shift(1)

    # Physique des aurores
    df["bz_negative"] = np.where(df["bz_component"].isna(), np.nan, (df["bz_component"] < 0).astype(int))

    # Cible
    df["aurora_visible"] = (df["kp_index"] >= 5).astype(int)

    return df

# -------------------------------------------------
# MAIN PROCESS
# -------------------------------------------------

def main():
    log.info("=== DÉMARRAGE PIPELINE OMNI HAPI (SANS FILTRE PARAMÉTRIQUE) ===")
    
    df = collect_all_years(YEARS)
    if df.empty:
        log.error("Aucune donnée récupérée. Le serveur NASA est peut-être down.")
        return
        
    log.info(f"Données brutes concaténées : {len(df)} lignes.")
        
    df = apply_feature_engineering(df)
    
    # On ajoute dst_index et solar_wind_pressure à la liste des colonnes finales
    expected_cols = [
        "timestamp", "kp_index", "ap_index", "dst_index", "month", "season", "hour_interval",
        "solar_wind_speed", "solar_wind_density", "solar_wind_pressure", "bz_component",
        "is_solar_maximum", "kp_previous_interval", "bz_negative", "aurora_visible"
    ]
    
    df = df[[c for c in expected_cols if c in df.columns]]
    
    if "kp_index" in df.columns:
        df = df.dropna(subset=["kp_index"])
        
    csv_path = os.path.join(DATA_DIR, "dataset_omni_final.csv")
    df.to_csv(csv_path, index=False)
    log.info(f"✅ Export CSV réussi : {csv_path} ({len(df)} lignes)")
    log.info(f"📈 Aurores détectées (Classe 1) : {df['aurora_visible'].sum()}")

if __name__ == "__main__":
    main()
