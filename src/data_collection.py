"""
data_collection.py — Projet Aurores Boréales
=============================================
Collecte les données depuis :
  - NOAA SWPC   : indice Kp/Ap historique (fichiers annuels, accès libre)
  - NASA DONKI  : événements vent solaire (clé API dans .env)

Produit :
  - data/dataset.csv   (~14 600 lignes, 5 ans)
  - data/sample.csv    (100 premières lignes)

Usage :
  python src/data_collection.py
"""
# data_collection.py — version corrigée NOAA trimestrielle

"""
data_collection.py
Projet Aurores Boréales
"""

import os
import json
import time
import logging
import requests
import pandas as pd
import numpy as np

from datetime import datetime
from dotenv import load_dotenv

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

load_dotenv()

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

YEARS = [2019, 2020, 2021, 2022, 2023]

RAW_DIR = "data/raw"
DATA_DIR = "data"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

# -------------------------------------------------
# NOAA
# -------------------------------------------------

# -------------------------------------------------
# NOAA
# -------------------------------------------------

def parse_noaa_text(raw_text: str) -> pd.DataFrame:
    """Parse le format texte brut de la NOAA (DGD)"""
    rows = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(":"):
            continue
        parts = line.split()
        if len(parts) < 29:
            continue
        try:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            ap_index = float(parts[21])
            # Kp values are from index 22 to 29
            kp_values = []
            for i in range(22, 30):
                val = parts[i].replace("-1", " -1 ").split()
                kp_values.extend(val)
            kp_values = [float(k) for k in kp_values[:8] if float(k) >= 0]
            
            date = datetime(year, month, day)
            for idx, kp in enumerate(kp_values):
                ts = date + pd.Timedelta(hours=idx * 3)
                rows.append({"timestamp": ts, "kp_index": kp, "ap_index": ap_index})
        except Exception:
            continue
    return pd.DataFrame(rows)

def fetch_noaa_quarter(year: int, quarter: int) -> pd.DataFrame:
    """Télécharge et stocke les données NOAA en JSON"""
    json_filename = f"{year}Q{quarter}_DGD.json"
    json_path = os.path.join(RAW_DIR, json_filename)
    
    if os.path.exists(json_path):
        log.info(f"[NOAA] cache JSON trouvé : {json_filename}")
        df = pd.read_json(json_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    # Si pas de JSON, on regarde si on a l'ancien TXT pour le convertir
    txt_path = json_path.replace(".json", ".txt")
    raw_text = ""
    
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        url = f"https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/annual_reports/daily_solar_indices_summaries/daily_geomagnetic_data/{os.path.basename(txt_path)}"
        log.info(f"[NOAA] téléchargement {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            raw_text = response.text
        except Exception as e:
            log.warning(f"[NOAA] erreur : {e}")
            return pd.DataFrame()

    df = parse_noaa_text(raw_text)
    if not df.empty:
        df.to_json(json_path, orient="records", indent=4, date_format="iso")
        if os.path.exists(txt_path): os.remove(txt_path) # Nettoyage
    return df

def fetch_all_noaa(years):
    frames = []
    for year in years:
        for quarter in range(1, 5):
            df = fetch_noaa_quarter(year, quarter)
            if not df.empty: frames.append(df)
    if not frames: raise RuntimeError("Aucune donnée NOAA collectée.")
    df = pd.concat(frames, ignore_index=True).sort_values("timestamp")
    log.info(f"[NOAA] total → {len(df)} lignes")
    return df

# -------------------------------------------------
# OMNI (ACE/DSCOVR)
# -------------------------------------------------

def fetch_omni_year(year: int) -> pd.DataFrame:
    """Télécharge et stocke les données OMNI en JSON"""
    json_filename = f"omni2_{year}.json"
    json_path = os.path.join(RAW_DIR, json_filename)
    
    if os.path.exists(json_path):
        log.info(f"[OMNI] cache JSON trouvé : {json_filename}")
        df = pd.read_json(json_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    dat_path = json_path.replace(".json", ".dat")
    raw_text = ""
    
    if os.path.exists(dat_path):
        with open(dat_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        url = f"https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_{year}.dat"
        log.info(f"[OMNI] téléchargement {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            if not (response.text.strip().startswith("<") or "<html>" in response.text.lower()):
                raw_text = response.text
        except Exception as e:
            log.warning(f"[OMNI] erreur : {e}")
            return pd.DataFrame()

    if not raw_text: return pd.DataFrame()
    
    # Parsing robuste
    import io
    try:
        raw_df = pd.read_csv(io.StringIO(raw_text), sep=r"\s+", header=None)
        res = pd.DataFrame()
        res["timestamp"] = pd.to_datetime(raw_df[0].astype(str) + "-" + raw_df[1].astype(str).str.zfill(3), format="%Y-%j")
        res["timestamp"] += pd.to_timedelta(raw_df[2], unit="h")
        res["bz_component"] = pd.to_numeric(raw_df[16], errors='coerce')
        res["solar_wind_density"] = pd.to_numeric(raw_df[23], errors='coerce')
        res["solar_wind_speed"] = pd.to_numeric(raw_df[24], errors='coerce')
        
        # NaNs
        res.loc[res["bz_component"] > 990, "bz_component"] = np.nan
        res.loc[res["solar_wind_density"] > 990, "solar_wind_density"] = np.nan
        res.loc[res["solar_wind_speed"] > 99990, "solar_wind_speed"] = np.nan
        df = res.dropna(subset=["bz_component", "solar_wind_density", "solar_wind_speed"], how="all")
        
        if not df.empty:
            df.to_json(json_path, orient="records", indent=4, date_format="iso")
            if os.path.exists(dat_path): os.remove(dat_path) # Nettoyage
        return df
    except Exception as e:
        log.error(f"[OMNI] erreur parsing : {e}")
        return pd.DataFrame()

def fetch_all_omni(years):
    frames = []
    for year in years:
        df = fetch_omni_year(year)
        if not df.empty:
            log.info(f"[OMNI] {year} → {len(df)} lignes")
            frames.append(df)
    if not frames: return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True).sort_values("timestamp")
    log.info(f"[OMNI] total → {len(df)} lignes")
    return df


# -------------------------------------------------
# NASA DONKI (Optionnel, conservé pour référence)
# -------------------------------------------------

def fetch_nasa_period(start_date: str, end_date: str):
    cache_name = f"nasa_wsa_{start_date}_{end_date}.json"
    cache_file = os.path.join(RAW_DIR, cache_name)

    if os.path.exists(cache_file):
        log.info(f"[NASA] cache trouvé {cache_name}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Utilisation de WSAEnlilSimulations car GST ne contient pas la vitesse/densité du vent solaire
    url = "https://api.nasa.gov/DONKI/WSAEnlilSimulations"

    params = {
        "startDate": start_date,
        "endDate": end_date,
        "api_key": NASA_API_KEY
    }

    log.info(f"[NASA] requête WSA {start_date} → {end_date}")

    try:
        response = requests.get(url, params=params, timeout=30)
        log.info(f"[NASA] HTTP {response.status_code}")
        response.raise_for_status()

        data = response.json()

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        log.info(f"[NASA] {len(data)} simulations trouvées")
        return data

    except requests.RequestException as e:
        log.warning(f"[NASA] erreur : {e}")
        return []


def parse_nasa(raw_simulations):
    rows = []

    for sim in raw_simulations:
        try:
            # 1. Vitesse de référence depuis cmeInputs
            fallback_speed = np.nan
            cme_inputs = sim.get("cmeInputs")
            if cme_inputs and len(cme_inputs) > 0:
                fallback_speed = float(cme_inputs[0].get("speed", np.nan) or np.nan)

            # 2. Chercher les impacts sur Terre
            impacts = sim.get("impactList") or []
            earth_impacts = [i for i in impacts if i.get("location") == "Earth"]

            if earth_impacts:
                for impact in earth_impacts:
                    ts_str = impact.get("arrivalTime")
                    if not ts_str:
                        continue
                    timestamp = datetime.strptime(ts_str[:16], "%Y-%m-%dT%H:%M")
                    
                    rows.append({
                        "timestamp": timestamp,
                        "solar_wind_speed": float(impact.get("speed", fallback_speed) or fallback_speed),
                        "solar_wind_density": float(impact.get("density", np.nan) or np.nan),
                        "bz_component": float(impact.get("bz", np.nan) or np.nan),
                    })
            
            # 3. Fallback : estimatedShockArrivalTime si Terre touchée
            elif sim.get("isEarthGB") or sim.get("isEarthMinorImpact"):
                ts_str = sim.get("estimatedShockArrivalTime")
                if ts_str:
                    timestamp = datetime.strptime(ts_str[:16], "%Y-%m-%dT%H:%M")
                    rows.append({
                        "timestamp": timestamp,
                        "solar_wind_speed": fallback_speed,
                        "solar_wind_density": np.nan,
                        "bz_component": np.nan,
                    })
        except Exception:
            continue

    return pd.DataFrame(rows)


def fetch_all_nasa(years):
    frames = []

    for year in years:
        periods = [
            (f"{year}-01-01", f"{year}-06-30"),
            (f"{year}-07-01", f"{year}-12-31")
        ]

        for start, end in periods:
            raw = fetch_nasa_period(start, end)

            if raw:
                df = parse_nasa(raw)

                if not df.empty:
                    frames.append(df)

            time.sleep(1)

    if not frames:
        log.warning("[NASA] aucune donnée collectée")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("timestamp").drop_duplicates().reset_index(drop=True)

    log.info(f"[NASA] total → {len(df)} événements")
    return df


# -------------------------------------------------
# FEATURE ENGINEERING
# -------------------------------------------------

def add_features(df):
    df = df.copy()

    df["month"] = df["timestamp"].dt.month

    def season(m):
        if m in [12, 1, 2]:
            return "hiver"
        elif m in [3, 4, 5]:
            return "printemps"
        elif m in [6, 7, 8]:
            return "ete"
        return "automne"

    df["season"] = df["month"].apply(season)

    df["hour_interval"] = df["timestamp"].dt.hour.apply(
        lambda h: f"{h:02d}h-{h+3:02d}h"
    )

    df["is_solar_maximum"] = df["timestamp"].dt.year.apply(
        lambda y: 1 if y >= 2023 else 0
    )

    df["kp_previous_interval"] = df["kp_index"].shift(1)

    if "bz_component" not in df.columns:
        df["bz_component"] = np.nan

    df["bz_negative"] = (df["bz_component"] < 0).astype(int)
    df["aurora_visible"] = (df["kp_index"] >= 5).astype(int)

    return df


# -------------------------------------------------
# MERGE
# -------------------------------------------------

def merge_noaa_nasa(df_noaa, df_nasa):
    if df_nasa.empty:
        df_noaa["solar_wind_speed"] = np.nan
        df_noaa["solar_wind_density"] = np.nan
        df_noaa["bz_component"] = np.nan
        return df_noaa

    merged = pd.merge_asof(
        df_noaa.sort_values("timestamp"),
        df_nasa.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("24h")
    )

    # Diagnostic
    n_matches = merged["solar_wind_speed"].notna().sum()
    log.info(f"[Fusion] {n_matches} correspondances NASA trouvées sur {len(merged)} lignes NOAA.")

    return merged


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    print("=" * 50)
    print("PROJET AURORES BORÉALES")
    print("=" * 50)

    print("\n-- Collecte NOAA --")
    df_noaa = fetch_all_noaa(YEARS)

    print("\n-- Collecte OMNI (ACE/DSCOVR) --")
    df_omni = fetch_all_omni(YEARS)

    print("\n-- Fusion --")
    # On utilise maintenant OMNI à la place de NASA DONKI pour la fusion
    df = merge_noaa_nasa(df_noaa, df_omni)

    print("\n-- Feature engineering --")
    df = add_features(df)

    final_columns = [
        "timestamp",
        "kp_index",
        "ap_index",
        "solar_wind_speed",
        "solar_wind_density",
        "bz_component",
        "month",
        "season",
        "hour_interval",
        "is_solar_maximum",
        "kp_previous_interval",
        "bz_negative",
        "aurora_visible"
    ]

    df = df[[c for c in final_columns if c in df.columns]]

    dataset_path = os.path.join(DATA_DIR, "dataset.csv")
    sample_path = os.path.join(DATA_DIR, "sample.csv")

    df.to_csv(dataset_path, index=False)
    df.head(100).to_csv(sample_path, index=False)

    print(f"\n[OK] dataset exporté : {dataset_path}")
    print(f"[OK] sample exporté  : {sample_path}")
    print(f"Total lignes : {len(df)}")


if __name__ == "__main__":
    main()