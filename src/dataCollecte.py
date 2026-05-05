"""
dataCollecte.py — Version FINALE STABLE (AMDA CSV + Sunspots)
============================================================
Collecte les données depuis :
  - NOAA SWPC   : Kp/Ap
  - AMDA HAPI   : Vent solaire + Sunspots (Format CSV Stable)
"""

import os
import time
import logging
import requests
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime
from dateutil.relativedelta import relativedelta

# -------------------------------------------------
# CONFIG
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

HAPI_BASE    = "http://amda.irap.omp.eu/service/hapi"
HAPI_DATASET = "omni-hour-all"
HAPI_PARAMS  = "omni_sw_v,omni_sw_n,omni_imf,omni_sunspots"
AMDA_FILL    = -1.0e+31

# -------------------------------------------------
# NOAA — Indice Kp/Ap
# -------------------------------------------------

def fetch_noaa_quarter(year: int, quarter: int) -> str:
    filename = f"{year}Q{quarter}_DGD.txt"
    cache_file = os.path.join(RAW_DIR, filename)
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    base_url = "https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/annual_reports/daily_solar_indices_summaries/daily_geomagnetic_data"
    url = f"{base_url}/{filename}"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(r.text)
        return r.text
    except Exception as e:
        log.error(f"[NOAA] erreur {filename} : {e}")
        return ""

def parse_noaa_quarter(raw_text: str, year: int) -> pd.DataFrame:
    import re
    rows = []
    for line in raw_text.splitlines():
        if not line.strip() or not line.strip().startswith(str(year)):
            continue
        nums = re.findall(r"-?\d+", line)
        if len(nums) < 30: continue
        try:
            mm, dd = int(nums[1]), int(nums[2])
            date = datetime(year, mm, dd)
            planetary = nums[-9:]
            ap_val = float(planetary[0])
            kp_vals = planetary[1:]
            for i, h in enumerate([0, 3, 6, 9, 12, 15, 18, 21]):
                rows.append({
                    "timestamp": date + pd.Timedelta(hours=h),
                    "kp_index": float(kp_vals[i]),
                    "ap_index": ap_val
                })
        except: continue
    return pd.DataFrame(rows)

def fetch_all_noaa(years: list):
    frames = []
    for y in years:
        for q in range(1, 5):
            raw = fetch_noaa_quarter(y, q)
            if raw:
                df = parse_noaa_quarter(raw, y)
                if not df.empty: frames.append(df)
    return pd.concat(frames).sort_values("timestamp").reset_index(drop=True)

# -------------------------------------------------
# AMDA HAPI — Vent solaire (Format CSV Stable)
# -------------------------------------------------

def fetch_amda_year(year: int) -> pd.DataFrame:
    """Télécharge une année via AMDA au format CSV."""
    start_str = f"{year}-01-01T00:00:00Z"
    end_str   = f"{year+1}-01-01T00:00:00Z"

    cache_name = f"amda_omni_stable_sci_{year}.csv"
    cache_file = os.path.join(RAW_DIR, cache_name)

    if os.path.exists(cache_file):
        log.info(f"[AMDA] cache trouvé : {cache_name}")
        return pd.read_csv(cache_file, parse_dates=["timestamp"])

    url = f"{HAPI_BASE}/data"
    params = {
        "id": HAPI_DATASET,
        "parameters": HAPI_PARAMS,
        "time.min": start_str,
        "time.max": end_str,
        "format": "csv"
    }

    log.info(f"[AMDA] requête CSV {year}...")
    try:
        r = requests.get(url, params=params, timeout=120)
        r.raise_for_status()
        
        lines = [l for l in r.text.splitlines() if not l.startswith("#")]
        
        # Structure AMDA CSV : timestamp, v, n, bx, by, bz, sunspots
        df = pd.read_csv(StringIO("\n".join(lines)), header=None, 
                         names=["timestamp", "v", "n", "bx", "by", "bz", "ss"])
        
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
        
        df = df.rename(columns={
            "v": "solar_wind_speed",
            "n": "solar_wind_density",
            "bz": "bz_component",
            "ss": "sunspot_number"
        })
        
        for col in ["solar_wind_speed", "solar_wind_density", "bz_component", "sunspot_number"]:
            df[col] = df[col].apply(lambda x: np.nan if x <= AMDA_FILL else x)

        df = df[["timestamp", "solar_wind_speed", "solar_wind_density", "bz_component", "sunspot_number"]]
        df.to_csv(cache_file, index=False)
        return df
    except Exception as e:
        log.error(f"[AMDA] erreur CSV {year} : {e}")
        return pd.DataFrame()

def fetch_all_amda(years: list):
    frames = []
    for y in years:
        df = fetch_amda_year(y)
        if not df.empty: 
            frames.append(df)
            log.info(f"[AMDA] {y} chargé ({len(df)} lignes)")
        time.sleep(1)
    if not frames: return pd.DataFrame()
    return pd.concat(frames).sort_values("timestamp").reset_index(drop=True)

# -------------------------------------------------
# FEATURE ENGINEERING
# -------------------------------------------------

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    df["month"] = df["timestamp"].dt.month
    def get_season(m):
        if m in [12, 1, 2]: return "hiver"
        if m in [3, 4, 5]:  return "printemps"
        if m in [6, 7, 8]:  return "ete"
        return "automne"
    df["season"] = df["month"].apply(get_season)
    df["hour_interval"] = df["timestamp"].dt.hour.apply(lambda h: f"{h:02d}h-{h+3:02d}h")

    # Cycle solaire scientifique
    df["sunspot_number"] = df["sunspot_number"].fillna(0)
    df["is_solar_maximum"] = (df["sunspot_number"] > 100).astype(int)

    df["kp_previous_interval"] = df["kp_index"].shift(1)
    df["bz_negative"] = np.where(df["bz_component"].isna(), np.nan, (df["bz_component"] < 0).astype(float))
    df["aurora_visible"] = (df["kp_index"] >= 5).astype(int)

    return df

# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    log.info("=== DEMARRAGE COLLECTE (STABLE : CSV + FEATURES) ===")
    
    df_noaa = fetch_all_noaa(YEARS)
    df_amda = fetch_all_amda(YEARS)

    if df_amda.empty:
        log.error("Fin : AMDA n'a renvoyé aucune donnée. Vérifiez votre connexion.")
        return

    # Fusion
    df = pd.merge_asof(
        df_noaa.sort_values("timestamp"),
        df_amda.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("3h")
    )

    df = add_features(df)

    final_cols = [
        "timestamp", "solar_wind_speed", "solar_wind_density", "bz_component",
        "sunspot_number", "month", "season", "hour_interval", "is_solar_maximum",
        "kp_previous_interval", "bz_negative", "kp_index", "ap_index", "aurora_visible"
    ]
    df = df[[c for c in final_cols if c in df.columns]]
    df = df.dropna(subset=["kp_index"])

    dataset_path = os.path.join(DATA_DIR, "dataset_final.csv")
    df.to_csv(dataset_path, index=False)
    
    log.info(f"✅ TERMINÉ : {len(df)} lignes dans data/dataset_final.csv")
    log.info(f"📈 Distribution Kp >= 5 : {df['aurora_visible'].sum()} événements")

if __name__ == "__main__":
    main()