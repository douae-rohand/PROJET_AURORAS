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

def fetch_noaa_quarter(year: int, quarter: int) -> str:
    filename = f"{year}Q{quarter}_DGD.txt"
    cache_file = os.path.join(RAW_DIR, filename)

    if os.path.exists(cache_file):
        log.info(f"[NOAA] cache trouvé : {filename}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    url = (
        "https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/"
        "annual_reports/daily_solar_indices_summaries/"
        f"daily_geomagnetic_data/{filename}"
    )

    log.info(f"[NOAA] téléchargement {filename}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(response.text)

        return response.text

    except requests.RequestException as e:
        log.warning(f"[NOAA] erreur {filename} : {e}")
        return ""


def parse_noaa_quarter(raw_text: str) -> pd.DataFrame:
    rows = []

    for line in raw_text.splitlines():
        line = line.strip()

        if (
            not line
            or line.startswith("#")
            or line.startswith(":")
        ):
            continue

        parts = line.split()

        # Format attendu :
        # YYYY MM DD + données...
        if len(parts) < 29:
            continue

        try:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])

            # bloc planétaire commence à index 21
            ap_index = float(parts[21])

            kp_values = []
            for i in range(22, 30):
                val = parts[i].replace("-1", " -1 ").split()
                kp_values.extend(val)

            kp_values = kp_values[:8]

            date = datetime(year, month, day)

            for idx, kp_raw in enumerate(kp_values):
                try:
                    kp = float(kp_raw)
                except ValueError:
                    continue

                if kp < 0:
                    continue

                ts = date + pd.Timedelta(hours=idx * 3)

                rows.append({
                    "timestamp": ts,
                    "kp_index": kp,
                    "ap_index": ap_index
                })

        except Exception:
            continue

    return pd.DataFrame(rows)


def fetch_all_noaa(years):
    frames = []

    for year in years:
        yearly = []

        for quarter in range(1, 5):
            raw = fetch_noaa_quarter(year, quarter)

            if raw:
                df = parse_noaa_quarter(raw)

                if not df.empty:
                    yearly.append(df)

            time.sleep(0.3)

        if yearly:
            df_year = pd.concat(yearly, ignore_index=True)
            log.info(f"[NOAA] {year} → {len(df_year)} lignes")
            frames.append(df_year)

    if not frames:
        raise RuntimeError("Aucune donnée NOAA collectée.")

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    log.info(f"[NOAA] total → {len(df)} lignes")
    return df


# -------------------------------------------------
# NASA
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
        tolerance=pd.Timedelta("6h")
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

    print("\n── Collecte NOAA ──")
    df_noaa = fetch_all_noaa(YEARS)

    print("\n── Collecte NASA ──")
    df_nasa = fetch_all_nasa(YEARS)

    print("\n── Fusion ──")
    df = merge_noaa_nasa(df_noaa, df_nasa)

    print("\n── Feature engineering ──")
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

    print(f"\n✅ dataset exporté : {dataset_path}")
    print(f"✅ sample exporté  : {sample_path}")
    print(f"Total lignes : {len(df)}")


if __name__ == "__main__":
    main()