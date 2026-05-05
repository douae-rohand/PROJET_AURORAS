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

import os
import re
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# 0. Configuration
# ─────────────────────────────────────────────

load_dotenv()
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

YEARS = [2019, 2020, 2021, 2022, 2023]

OUTPUT_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 1. NOAA — Kp / Ap
# ─────────────────────────────────────────────


def fetch_noaa_kp_year(year: int) -> pd.DataFrame:
    """
    Télécharge les 4 fichiers trimestriels NOAA
    et extrait les Kp planétaires toutes les 3 heures.
    """
    base_url = (
        "https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/"
        "annual_reports/daily_solar_indices_summaries/daily_geomagnetic_data"
    )

    rows = []

    for quarter in range(1, 5):
        url = f"{base_url}/{year}Q{quarter}_DGD.txt"
        print(f"  [NOAA] Téléchargement {year} Q{quarter}...")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  [NOAA] Erreur {year} Q{quarter}: {e}")
            continue

        for line in response.text.splitlines():
            line = line.strip()

            if not line:
                continue

            # garder seulement les lignes qui commencent par l'année
            if not line.startswith(str(year)):
                continue

            # extrait tous les entiers (gère aussi les valeurs collées comme 3-1-1)
            nums = re.findall(r"-?\d+", line)

            # format attendu :
            # 3 nombres date + 9 middle + 9 high + 9 planetary = 30
            if len(nums) < 30:
                continue

            try:
                yyyy, mm, dd = map(int, nums[:3])
                date = datetime(yyyy, mm, dd)
            except ValueError:
                continue

            # Les 9 derniers = Planetary A + 8 Kp
            planetary = nums[-9:]

            try:
                ap_val = float(planetary[0])
            except ValueError:
                ap_val = np.nan

            kp_values = planetary[1:]

            for i, hour in enumerate([0, 3, 6, 9, 12, 15, 18, 21]):
                try:
                    kp_val = float(kp_values[i])
                except (ValueError, IndexError):
                    continue

                rows.append({
                    "timestamp": date + timedelta(hours=hour),
                    "kp_index": kp_val,
                    "ap_index": ap_val if ap_val >= 0 else np.nan,
                })

        time.sleep(0.2)

    df = pd.DataFrame(rows)

    if df.empty:
        print(f"  [NOAA] {year} → 0 ligne")
        return df

    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    print(f"  [NOAA] {year} → {len(df)} lignes collectées")
    return df



def fetch_all_noaa(years: list) -> pd.DataFrame:
    frames = []

    for year in years:
        df = fetch_noaa_kp_year(year)
        if not df.empty:
            frames.append(df)
        time.sleep(0.5)

    if not frames:
        raise RuntimeError("Aucune donnée NOAA collectée.")

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values("timestamp").reset_index(drop=True)

    print(f"\n[NOAA] Total : {len(result)} lignes\n")
    return result


# ─────────────────────────────────────────────
# 2. NASA
# ─────────────────────────────────────────────


def fetch_nasa_wsaenlil(start_date: str, end_date: str) -> pd.DataFrame:
    url = "https://api.nasa.gov/DONKI/WSAEnlilSimulations"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "api_key": NASA_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return pd.DataFrame()

    rows = []

    for sim in data:
        try:
            ts = sim.get("modelCompletionTime")
            if not ts:
                continue

            timestamp = datetime.strptime(ts[:16], "%Y-%m-%dT%H:%M")

            for impact in sim.get("impactList", []):
                rows.append({
                    "timestamp": timestamp,
                    "solar_wind_speed": float(impact.get("speed", np.nan) or np.nan),
                    "solar_wind_density": np.nan,
                    "bz_component": float(impact.get("bz", np.nan) or np.nan),
                })
        except Exception:
            continue

    return pd.DataFrame(rows)



def fetch_all_nasa(years: list) -> pd.DataFrame:
    frames = []

    for year in years:
        for m_start, m_end in [("01-01", "06-30"), ("07-01", "12-31")]:
            start = f"{year}-{m_start}"
            end = f"{year}-{m_end}"

            df = fetch_nasa_wsaenlil(start, end)
            if not df.empty:
                frames.append(df)

            time.sleep(1)

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    result = result.drop_duplicates(subset=["timestamp"])
    result = result.sort_values("timestamp").reset_index(drop=True)

    return result


# ─────────────────────────────────────────────
# 3. Feature engineering
# ─────────────────────────────────────────────

SOLAR_MAXIMA_YEARS = {2023, 2024, 2025}



def get_season(month: int) -> str:
    if month in (12, 1, 2):
        return "hiver"
    if month in (3, 4, 5):
        return "printemps"
    if month in (6, 7, 8):
        return "ete"
    return "automne"



def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["month"] = df["timestamp"].dt.month
    df["season"] = df["month"].apply(get_season)
    df["hour_interval"] = df["timestamp"].dt.hour.apply(
        lambda h: f"{h:02d}h-{(h + 3):02d}h"
    )

    df["is_solar_maximum"] = df["timestamp"].dt.year.apply(
        lambda y: 1 if y in SOLAR_MAXIMA_YEARS else 0
    )

    df = df.sort_values("timestamp").reset_index(drop=True)
    df["kp_previous_interval"] = df["kp_index"].shift(1)

    if "bz_component" in df.columns:
        df["bz_negative"] = (df["bz_component"] < 0).astype(int)
    else:
        df["bz_negative"] = np.nan

    df["aurora_visible"] = (df["kp_index"] >= 5).astype(int)

    return df


# ─────────────────────────────────────────────
# 4. Fusion
# ─────────────────────────────────────────────


def merge_noaa_nasa(df_noaa: pd.DataFrame, df_nasa: pd.DataFrame) -> pd.DataFrame:
    if df_nasa.empty:
        df_noaa["solar_wind_speed"] = np.nan
        df_noaa["solar_wind_density"] = np.nan
        df_noaa["bz_component"] = np.nan
        return df_noaa

    df_nasa = df_nasa[[
        "timestamp",
        "solar_wind_speed",
        "solar_wind_density",
        "bz_component",
    ]].drop_duplicates("timestamp")

    return pd.merge_asof(
        df_noaa.sort_values("timestamp"),
        df_nasa.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("6h"),
    )


# ─────────────────────────────────────────────
# 5. Main
# ─────────────────────────────────────────────


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

    dataset_path = os.path.join(OUTPUT_DIR, "dataset.csv")
    sample_path = os.path.join(OUTPUT_DIR, "sample.csv")

    df.to_csv(dataset_path, index=False)
    df.head(100).to_csv(sample_path, index=False)

    print(f"\n✅ dataset exporté : {dataset_path}")
    print(f"✅ sample exporté  : {sample_path}")
    print(f"Total lignes : {len(df)}")


if __name__ == "__main__":
    main()
