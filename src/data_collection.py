"""
data_collection.py — Projet Aurores Boréales
=============================================
Collecte les données depuis :
  - NOAA SWPC   : indice Kp/Ap historique (fichiers annuels, accès libre)
  - NASA HAPI   : vent solaire continu via OMNIWeb (flow_speed, proton_density, BZ_GSM)

Produit :
  - data/dataset.csv   (~14 600 lignes, 5 ans)
  - data/sample.csv    (100 premières lignes)

Usage :
  python src/data_collection.py
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

# Valeurs fill NASA HAPI à remplacer par NaN
NASA_FILL_VALUES = {
    "flow_speed":     99999.9,
    "proton_density": 999.99,
    "BZ_GSM":         9999.99,
}

# -------------------------------------------------
# NOAA — Indice Kp/Ap
# -------------------------------------------------

def fetch_noaa_quarter(year: int, quarter: int) -> str:
    """
    Télécharge un fichier trimestriel NOAA (archive NGDC stable).
    Format : {year}Q{quarter}_DGD.txt
    """
    filename = f"{year}Q{quarter}_DGD.txt"
    cache_file = os.path.join(RAW_DIR, filename)

    if os.path.exists(cache_file):
        log.info(f"[NOAA] cache trouvé : {filename}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()

    base_url = (
        "https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/"
        "annual_reports/daily_solar_indices_summaries/daily_geomagnetic_data"
    )
    url = f"{base_url}/{filename}"
    log.info(f"[NOAA] téléchargement {url}")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        return response.text
    except requests.RequestException as e:
        log.error(f"[NOAA] erreur {filename} : {e}")
        return ""


def parse_noaa_quarter(raw_text: str, year: int) -> pd.DataFrame:
    """Parse le format trimestriel NOAA."""
    import re
    rows = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line or not line.startswith(str(year)):
            continue

        # Extraction de tous les entiers de la ligne
        nums = re.findall(r"-?\d+", line)

        # Format attendu : au moins 30 colonnes (Date + Données + Kp/Ap)
        if len(nums) < 30:
            continue

        try:
            mm, dd = int(nums[1]), int(nums[2])
            date = datetime(year, mm, dd)

            # Les 9 dernières valeurs : Ap planétaire + 8 Kp
            planetary = nums[-9:]
            ap_val = float(planetary[0])
            kp_values = planetary[1:]

            for i, hour in enumerate([0, 3, 6, 9, 12, 15, 18, 21]):
                kp_val = float(kp_values[i])
                if kp_val < 0: continue

                rows.append({
                    "timestamp": date + pd.Timedelta(hours=hour),
                    "kp_index": kp_val,
                    "ap_index": ap_val if ap_val >= 0 else np.nan,
                })
        except Exception:
            continue

    return pd.DataFrame(rows)


def fetch_all_noaa(years: list) -> pd.DataFrame:
    """Collecte les données NOAA trimestrielles."""
    frames = []

    for year in years:
        for quarter in range(1, 5):
            raw = fetch_noaa_quarter(year, quarter)
            if raw:
                df = parse_noaa_quarter(raw, year)
                if not df.empty:
                    frames.append(df)
            time.sleep(0.1)

    if not frames:
        raise RuntimeError("[NOAA] Aucune donnée collectée.")

    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    log.info(f"[NOAA] TOTAL → {len(df)} lignes")
    return df


# -------------------------------------------------
# NASA HAPI — Vent solaire continu (OMNIWeb)
# -------------------------------------------------

HAPI_BASE    = "https://cdaweb.gsfc.nasa.gov/hapi"
HAPI_DATASET = "OMNI_HRO_5MIN"
HAPI_PARAMS  = "flow_speed,proton_density,BZ_GSM"


def fetch_hapi_month(year: int, month: int) -> pd.DataFrame:
    """
    Télécharge les données HAPI pour un mois complet en découpant par tranches de 10 jours
    pour éviter les Timeouts serveurs.
    """
    cache_name = f"hapi_5min_{year}_{month:02d}.csv"
    cache_file = os.path.join(RAW_DIR, cache_name)

    if os.path.exists(cache_file):
        log.info(f"[HAPI] cache trouvé : {cache_name}")
        try:
            return pd.read_csv(cache_file, parse_dates=["timestamp"])
        except Exception:
            os.remove(cache_file)

    # Définition des tranches de 10 jours
    ranges = [
        (1, 10), (11, 20), (21, 31)
    ]
    
    month_frames = []
    
    for start_day, end_day in ranges:
        # Ajustement pour la fin de mois
        try:
            start_date = datetime(year, month, start_day)
            # Pour la fin du mois, on va jusqu'au 1er du mois suivant
            if end_day == 31:
                end_date = start_date + relativedelta(months=1)
                end_date = datetime(end_date.year, end_date.month, 1)
            else:
                end_date = datetime(year, month, end_day + 1)
        except ValueError: # Cas où le mois a moins de 31 jours
            continue

        start_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str   = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        url = f"{HAPI_BASE}/data"
        params = {
            "id":         HAPI_DATASET,
            "parameters": HAPI_PARAMS,
            "time.min":   start_str,
            "time.max":   end_str,
            "format":     "csv",
        }

        max_retries = 2
        success = False
        for attempt in range(max_retries):
            try:
                log.info(f"[HAPI] {year}-{month:02d} | jours {start_day}-{end_day} (essai {attempt+1})")
                response = requests.get(url, params=params, timeout=60)
                response.raise_for_status()

                lines = [l for l in response.text.splitlines() if not l.startswith("#")]
                csv_text = "\n".join(lines)

                if csv_text.strip():
                    df_part = pd.read_csv(
                        StringIO(csv_text),
                        header=0,
                        names=["timestamp", "flow_speed", "proton_density", "BZ_GSM"]
                    )
                    month_frames.append(df_part)
                
                success = True
                break
            except Exception as e:
                log.warning(f"[HAPI] erreur tranche {start_day}-{end_day} : {e}")
                time.sleep(3)

    if not month_frames:
        return pd.DataFrame()

    df_month = pd.concat(month_frames, ignore_index=True)
    df_month["timestamp"] = pd.to_datetime(df_month["timestamp"], utc=True).dt.tz_localize(None)

    for col, fill_val in NASA_FILL_VALUES.items():
        if col in df_month.columns:
            df_month[col] = df_month[col].replace(fill_val, np.nan)
            df_month.loc[df_month[col] > fill_val * 0.9, col] = np.nan

    df_month.to_csv(cache_file, index=False)
    log.info(f"[HAPI] {year}-{month:02d} terminé → {len(df_month)} lignes")
    return df_month


def fetch_all_hapi(years: list) -> pd.DataFrame:
    """
    Collecte toutes les données HAPI par mois et les agrège en tranches de 3h
    pour correspondre à la granularité NOAA.
    """
    frames = []

    for year in years:
        for month in range(1, 13):
            df = fetch_hapi_month(year, month)

            if not df.empty:
                frames.append(df)

            time.sleep(1)  # 1 seconde entre chaque requête

    if not frames:
        log.warning("[HAPI] aucune donnée collectée")
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)
    df_all = df_all.sort_values("timestamp").reset_index(drop=True)

    log.info(f"[HAPI] total avant agrégation → {len(df_all)} mesures à la minute")

    # ---- Agrégation en tranches de 3h ----
    # On crée une clé de tranche : on arrondit le timestamp à la tranche de 3h inférieure
    df_all["tranche_3h"] = df_all["timestamp"].dt.floor("3h")

    df_3h = df_all.groupby("tranche_3h").agg(
        solar_wind_speed=("flow_speed",     "mean"),
        solar_wind_density=("proton_density", "mean"),
        bz_component=("BZ_GSM",         "mean"),
    ).reset_index()

    df_3h = df_3h.rename(columns={"tranche_3h": "timestamp"})

    log.info(f"[HAPI] après agrégation 3h → {len(df_3h)} lignes")

    # Rapport sur les valeurs manquantes
    for col in ["solar_wind_speed", "solar_wind_density", "bz_component"]:
        pct_nan = df_3h[col].isna().mean() * 100
        log.info(f"[HAPI] NaN {col} : {pct_nan:.1f}%")

    return df_3h


# -------------------------------------------------
# FUSION NOAA + HAPI
# -------------------------------------------------

def merge_noaa_hapi(df_noaa: pd.DataFrame, df_hapi: pd.DataFrame) -> pd.DataFrame:
    """
    Fusionne les données NOAA (Kp/Ap) avec les données HAPI (vent solaire).
    Utilise merge_asof avec une tolérance de 3h car les deux sources
    sont maintenant à la même granularité temporelle.
    """
    if df_hapi.empty:
        log.warning("[Fusion] HAPI vide, colonnes vent solaire seront NaN")
        df_noaa["solar_wind_speed"]   = np.nan
        df_noaa["solar_wind_density"] = np.nan
        df_noaa["bz_component"]       = np.nan
        return df_noaa

    merged = pd.merge_asof(
        df_noaa.sort_values("timestamp"),
        df_hapi.sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
        tolerance=pd.Timedelta("3h")
    )

    n_matches = merged["solar_wind_speed"].notna().sum()
    pct = n_matches / len(merged) * 100
    log.info(f"[Fusion] {n_matches}/{len(merged)} correspondances NASA ({pct:.1f}%)")

    return merged


# -------------------------------------------------
# FEATURE ENGINEERING
# -------------------------------------------------

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit les features supplémentaires.

    IMPORTANT — Ordre critique pour éviter le leakage :
    1. kp_previous_interval est construit avec shift(1) AVANT aurora_visible
    2. aurora_visible est construit EN DERNIER
    3. kp_index et ap_index restent dans le CSV pour traçabilité
       mais NE DOIVENT PAS être utilisés comme features en Phase 2
    """
    df = df.copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    # --- Features temporelles ---
    df["month"] = df["timestamp"].dt.month

    def get_season(m):
        if m in [12, 1, 2]:   return "hiver"
        if m in [3, 4, 5]:    return "printemps"
        if m in [6, 7, 8]:    return "ete"
        return "automne"

    df["season"]        = df["month"].apply(get_season)
    df["hour_interval"] = df["timestamp"].dt.hour.apply(
        lambda h: f"{h:02d}h-{h+3:02d}h"
    )

    # --- Cycle solaire ---
    # Cycle 25 : minimum fin 2019, maximum estimé fin 2024
    # On code les années proches du maximum comme is_solar_maximum=1
    solar_max_years = {2022, 2023, 2024}
    df["is_solar_maximum"] = df["timestamp"].dt.year.apply(
        lambda y: 1 if y in solar_max_years else 0
    )

    # --- Feature lag Kp (shift temporel) ---
    # kp_previous_interval = Kp de la tranche précédente (3h avant)
    # Le shift(1) garantit qu'on n'utilise PAS d'information future
    df["kp_previous_interval"] = df["kp_index"].shift(1)

    # --- Feature Bz négatif ---
    # Bz < 0 est physiquement favorable aux aurores (reconnexion magnétique)
    # On gère le cas NaN explicitement
    df["bz_negative"] = np.where(
        df["bz_component"].isna(),
        np.nan,
        (df["bz_component"] < 0).astype(float)
    )

    # --- Variable cible (TOUJOURS EN DERNIER) ---
    # aurora_visible = 1 si Kp >= 5 (définition scientifique standard)
    # ATTENTION : kp_index et ap_index ne doivent PAS être dans X en Phase 2
    df["aurora_visible"] = (df["kp_index"] >= 5).astype(int)

    return df


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():
    print("=" * 55)
    print("  PROJET AURORES BORÉALES — Collecte des données")
    print("=" * 55)

    # ── 1. NOAA ──
    print("\n[1/4] Collecte NOAA (Kp/Ap)...")
    df_noaa = fetch_all_noaa(YEARS)
    print(f"      → {len(df_noaa)} lignes collectées")

    # ── 2. NASA HAPI ──
    print("\n[2/4] Collecte NASA HAPI (vent solaire continu)...")
    df_hapi = fetch_all_hapi(YEARS)
    print(f"      → {len(df_hapi)} tranches de 3h collectées")

    # ── 3. Fusion ──
    print("\n[3/4] Fusion NOAA + HAPI...")
    df = merge_noaa_hapi(df_noaa, df_hapi)
    print(f"      → {len(df)} lignes après fusion")

    # ── 4. Feature engineering ──
    print("\n[4/4] Feature engineering...")
    df = add_features(df)

    # ── Colonnes finales ──
    # kp_index et ap_index sont gardés pour traçabilité
    # mais annotés comme NON-FEATURES dans DATASET.md
    final_columns = [
        "timestamp",
        # === FEATURES D'ENTRAÎNEMENT (X) ===
        "solar_wind_speed",      # NASA HAPI
        "solar_wind_density",    # NASA HAPI
        "bz_component",          # NASA HAPI
        "month",                 # NOAA dérivé
        "season",                # NOAA dérivé
        "hour_interval",         # NOAA dérivé
        "is_solar_maximum",      # dérivé
        "kp_previous_interval",  # NOAA lag
        "bz_negative",           # dérivé de bz_component
        # === COLONNES SOURCES (traçabilité uniquement, exclure de X) ===
        "kp_index",              # SOURCE de aurora_visible — NE PAS utiliser en X
        "ap_index",              # CORRÉLÉ à kp_index — NE PAS utiliser en X
        # === VARIABLE CIBLE (y) ===
        "aurora_visible",
    ]

    df = df[[c for c in final_columns if c in df.columns]]

    # Supprimer les lignes sans valeur Kp (impossible de construire la cible)
    df = df.dropna(subset=["kp_index", "aurora_visible"])
    df = df.reset_index(drop=True)

    # ── Export ──
    dataset_path = os.path.join(DATA_DIR, "dataset.csv")
    sample_path  = os.path.join(DATA_DIR, "sample.csv")

    df.to_csv(dataset_path, index=False)
    df.head(100).to_csv(sample_path, index=False)

    # ── Résumé ──
    print("\n" + "=" * 55)
    print("  RÉSUMÉ DU DATASET")
    print("=" * 55)
    print(f"  Lignes totales     : {len(df)}")
    print(f"  Colonnes           : {len(df.columns)}")
    print(f"  Période            : {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"\n  Distribution cible :")
    vc = df["aurora_visible"].value_counts()
    print(f"    Classe 0 (Kp < 5) : {vc.get(0, 0)} ({vc.get(0, 0)/len(df)*100:.1f}%)")
    print(f"    Classe 1 (Kp ≥ 5) : {vc.get(1, 0)} ({vc.get(1, 0)/len(df)*100:.1f}%)")
    print(f"\n  NaN par feature :")
    for col in ["solar_wind_speed", "solar_wind_density", "bz_component", "bz_negative", "kp_previous_interval"]:
        if col in df.columns:
            pct = df[col].isna().mean() * 100
            print(f"    {col:<25} : {pct:.1f}%")
    print(f"\n  ✅ Dataset exporté : {dataset_path}")
    print(f"  ✅ Sample exporté  : {sample_path}")
    print("=" * 55)


if __name__ == "__main__":
    main()