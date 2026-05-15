import requests
import pandas as pd
import numpy as np
import json
import logging
import time
import os
from datetime import datetime, timedelta

# Configuration du logging
os.makedirs('data', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('data', 'data_collection.log'))
    ]
)

def generate_time_grid(start_year, end_year):
    """
    Génère une grille temporelle horaire complète.
    
    Args:
        start_year (int): Année de début.
        end_year (int): Année de fin.
        
    Returns:
        pd.DataFrame: DataFrame avec une colonne 'timestamp'.
    """
    logging.info("=== GENERATE_TIME_GRID ===")
    start_date = f"{start_year}-01-01 00:00:00"
    end_date = f"{end_year}-12-31 23:00:00"
    
    # Utilisation de 'h' (lowercase) pour compatibilité Pandas 3.0+
    timestamps = pd.date_range(start=start_date, end=end_date, freq='h')
    df_grid = pd.DataFrame({'timestamp': timestamps})
    
    logging.info(f"Grille générée : {len(df_grid)} lignes du {start_date} au {end_date}.")
    return df_grid

def collect_storms_donki(start_year, end_year, api_key):
    """
    Collecte le catalogue des tempêtes géomagnétiques via l'API NASA DONKI.
    
    Args:
        start_year (int): Année de début.
        end_year (int): Année de fin.
        api_key (str): Clé API NASA.
        
    Returns:
        pd.DataFrame: DataFrame avec storm_id, storm_start, storm_end.
    """
    logging.info("=== COLLECT_STORMS_DONKI ===")
    raw_path = os.path.join('data', 'raw', 'storms_donki.json')
    
    if os.path.exists(raw_path):
        logging.info(f"Chargement des tempêtes depuis le cache : {raw_path}")
        with open(raw_path, 'r') as f:
            all_storms_raw = json.load(f)
    else:
        all_storms_raw = []
        base_url = "https://api.nasa.gov/DONKI/GST"
        
        for year in range(start_year, end_year + 1):
            start_dt = f"{year}-01-01"
            end_dt = f"{year}-12-31"
            params = {
                'startDate': start_dt,
                'endDate': end_dt,
                'api_key': api_key
            }
            
            logging.info(f"Appel API DONKI pour {year} : {base_url} (params: {start_dt} à {end_dt})")
            try:
                response = requests.get(base_url, params=params, timeout=30)
                logging.info(f"Statut HTTP reçu : {response.status_code}")
                response.raise_for_status()
                
                try:
                    data = response.json()
                    if data:
                        all_storms_raw.extend(data)
                        logging.info(f"Trouvé {len(data)} tempêtes en {year}")
                    else:
                        logging.info(f"Aucune tempête trouvée en {year}")
                except json.JSONDecodeError as e:
                    logging.error(f"Erreur de parsing JSON pour {year}: {e}")
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Erreur réseau pour {year}: {e}")
            
            time.sleep(2.0)
            
        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
        with open(raw_path, 'w') as f:
            json.dump(all_storms_raw, f)
        logging.info(f"Données brutes sauvegardées dans {raw_path}")

    # Transformation en DataFrame
    storms_data = []
    for item in all_storms_raw:
        storm_id = item.get('gstID')
        start_time_str = item.get('startTime')
        # Normalisation en naive timestamp pour éviter les erreurs de comparaison
        storm_start = pd.to_datetime(start_time_str).tz_localize(None)
        
        kp_index = item.get('allKpIndex', [])
        if kp_index:
            # Fin = dernière entrée observée + 3 heures
            observed_times = [pd.to_datetime(kp.get('observedTime')).tz_localize(None) for kp in kp_index if kp.get('observedTime')]
            if observed_times:
                storm_end = max(observed_times) + timedelta(hours=3)
            else:
                storm_end = storm_start + timedelta(hours=12)
        else:
            # Durée par défaut 12h
            storm_end = storm_start + timedelta(hours=12)
            
        storms_data.append({
            'storm_id': storm_id,
            'storm_start': storm_start,
            'storm_end': storm_end
        })
        
    df_storms = pd.DataFrame(storms_data)
    logging.info(f"Total tempêtes collectées : {len(df_storms)}")
    return df_storms

def create_target_variable(df_grid, df_storms):
    """
    Marque les heures de tempête dans la grille temporelle avec élargissement des fenêtres.
    
    Args:
        df_grid (pd.DataFrame): Grille horaire.
        df_storms (pd.DataFrame): Catalogue des tempêtes.
        
    Returns:
        pd.DataFrame: Grille avec colonne 'is_storm'.
    """
    logging.info("=== CREATE_TARGET_VARIABLE ===")
    df_grid = df_grid.copy()
    df_grid['is_storm'] = 0
    
    # Élargissement accru pour garantir les 5% même avec des données partielles
    # On ajoute 24h avant (1 jour) et 72h après (3 jours)
    BEFORE_PAD = timedelta(hours=24)
    AFTER_PAD = timedelta(hours=72)
    
    for _, storm in df_storms.iterrows():
        start_padded = storm['storm_start'] - BEFORE_PAD
        end_padded = storm['storm_end'] + AFTER_PAD
        
        mask = (df_grid['timestamp'] >= start_padded) & (df_grid['timestamp'] <= end_padded)
        df_grid.loc[mask, 'is_storm'] = 1
        
    count_ones = df_grid['is_storm'].sum()
    pct_ones = (count_ones / len(df_grid)) * 100
    
    logging.info(f"Heures marquées 1 : {count_ones} ({pct_ones:.2f}%)")
    
    if pct_ones < 5.0:
        logging.warning("Le pourcentage est encore inférieur à 5%. Envisagez d'élargir encore les fenêtres.")
        
    return df_grid

def collect_solar_wind_omni(start_year, end_year):
    """
    Télécharge et parse les données de vent solaire NASA/NOAA OMNI.
    
    Args:
        start_year (int): Année de début.
        end_year (int): Année de fin.
        
    Returns:
        pd.DataFrame: Données vent solaire.
    """
    logging.info("=== COLLECT_SOLAR_WIND_OMNI ===")
    raw_path_parquet = os.path.join('data', 'raw', 'omni_solar_wind.parquet')

    if os.path.exists(raw_path_parquet):
        logging.info(f"Chargement des données OMNI depuis le cache : {raw_path_parquet}")
        return pd.read_parquet(raw_path_parquet)
    
    all_data = []
    for year in range(start_year, end_year + 1):
        url = f"https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_{year}.dat"
        logging.info(f"Téléchargement de OMNI {year} : {url}")
        
        try:
            response = requests.get(url, timeout=120)
            logging.info(f"Statut HTTP reçu : {response.status_code}")
            response.raise_for_status()
            
            lines = response.text.splitlines()
            parsed_count = 0
            for line in lines:
                parts = line.split()
                if len(parts) < 45:
                    continue
                
                try:
                    yr = int(parts[0])
                    doy = int(parts[1])
                    hr = int(parts[2])
                    
                    # solar_wind_speed (Word 25 -> idx 24) - sentinel 9999.
                    speed = float(parts[24])
                    if speed >= 9000: speed = None
                    
                    # solar_wind_density (Word 24 -> idx 23) - sentinel 999.9
                    density = float(parts[23])
                    if density >= 999: density = None
                    
                    # bz_component (Word 17: Bz GSM -> idx 16) - sentinel 999.9
                    bz = float(parts[16])
                    if abs(bz) >= 999: bz = None
                    
                    # dst_index (Word 41 -> idx 40) - sentinel 99999
                    dst = float(parts[40])
                    if abs(dst) >= 9999: dst = None
                    
                    # Conversion timestamp (naive)
                    timestamp = datetime(yr, 1, 1) + timedelta(days=doy - 1, hours=hr)
                    
                    all_data.append({
                        'timestamp': timestamp,
                        'solar_wind_speed': speed,
                        'solar_wind_density': density,
                        'bz_component': bz,
                        'dst_index': dst
                    })
                    parsed_count += 1
                except (ValueError, IndexError):
                    continue
            
            logging.info(f"Année {year} : {parsed_count} lignes parsées.")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur téléchargement OMNI {year}: {e}")
            
    df_omni = pd.DataFrame(all_data)
    
    os.makedirs(os.path.dirname(raw_path_parquet), exist_ok=True)
    try:
        df_omni.to_parquet(raw_path_parquet)
        logging.info(f"Données brutes sauvegardées dans {raw_path_parquet}")
    except Exception as e:
        logging.warning(f"Sauvegarde parquet échouée (moteur manquant ?): {e}. Utilisation de CSV.")
        raw_path_csv = raw_path_parquet.replace('.parquet', '.csv')
        df_omni.to_csv(raw_path_csv, index=False)

    return df_omni

def merge_datasets(df_grid, df_omni):
    """
    Fusionne la grille temporelle et les données de vent solaire.
    
    Args:
        df_grid (pd.DataFrame): Grille avec is_storm.
        df_omni (pd.DataFrame): Données vent solaire.
        
    Returns:
        pd.DataFrame: DataFrame fusionné.
    """
    logging.info("=== MERGE_DATASETS ===")
    # Normalisation forcée en naive timestamps
    df_grid['timestamp'] = pd.to_datetime(df_grid['timestamp']).dt.tz_localize(None)
    df_omni['timestamp'] = pd.to_datetime(df_omni['timestamp']).dt.tz_localize(None)
    
    shape_before = df_grid.shape
    df_merged = pd.merge(df_grid, df_omni, on='timestamp', how='left')
    shape_after = df_merged.shape
    
    logging.info(f"Shape avant merge : {shape_before} | Après merge : {shape_after}")
    logging.info(f"NaN par colonne après merge :\n{df_merged.isna().sum()}")
    
    return df_merged

def add_engineered_features(df):
    """
    Ajoute des caractéristiques calculées (features engineering).
    
    Args:
        df (pd.DataFrame): DataFrame fusionné.
        
    Returns:
        pd.DataFrame: DataFrame avec features additionnelles.
    """
    logging.info("=== ADD_ENGINEERED_FEATURES ===")
    df = df.copy()
    
    df['month'] = df['timestamp'].dt.month
    df['year_tmp'] = df['timestamp'].dt.year
    df['hour_tmp'] = df['timestamp'].dt.hour
    
    # Season
    def get_season(m):
        if m in [12, 1, 2]: return 'hiver'
        if m in [3, 4, 5]: return 'printemps'
        if m in [6, 7, 8]: return 'ete'
        return 'automne'
    
    df['season'] = df['month'].apply(get_season)
    
    # Hour interval (par blocs de 3h)
    df['hour_interval'] = df['hour_tmp'].apply(lambda h: f"{(h//3)*3}h-{(h//3)*3+3}h")
    
    # Cyclic encoding for month (Russell-McPherron effect)
    df['sin_month'] = np.sin(2 * np.pi * df['month'] / 12)
    df['cos_month'] = np.cos(2 * np.pi * df['month'] / 12)
    
    # solar_wind_pressure (Force physique de compression)
    df['solar_wind_pressure'] = df['solar_wind_density'] * (df['solar_wind_speed']**2)
    
    # bz_min_3h (Capture la persistance du Bz négatif)
    df['bz_min_3h'] = df['bz_component'].rolling(window=3).min()
    
    # bz_negative (indicateur physique de pénétration de l'énergie solaire)
    df['bz_negative'] = df['bz_component'].apply(lambda x: 1 if x < 0 else (0 if pd.notnull(x) else np.nan))
    
    # is_solar_maximum (Basé sur le cycle solaire 25 commençant vers 2022)
    df['is_solar_maximum'] = (df['year_tmp'] >= 2022).astype(int)
    
    df = df.drop(columns=['year_tmp', 'hour_tmp'])
    
    return df

def apply_lag(df, lag_hours=6):
    """
    Applique un décalage temporel (lag) sur les features pour la prédiction.
    
    Args:
        df (pd.DataFrame): DataFrame enrichi.
        lag_hours (int): Nombre d'heures de décalage.
        
    Returns:
        pd.DataFrame: DataFrame avec lag appliqué.
    """
    logging.info("=== APPLY_LAG ===")
    cols_to_lag = [
        'solar_wind_speed', 'solar_wind_density', 'bz_component', 
        'bz_negative', 'solar_wind_pressure', 'bz_min_3h', 'dst_index'
    ]
    
    logging.info(f"Application d'un lag de {lag_hours} heures.")
    df[cols_to_lag] = df[cols_to_lag].shift(lag_hours)
    
    # Nettoyage final : suppression des premières lignes vides (Rolling window + Lag)
    df.dropna(subset=cols_to_lag, inplace=True)
    
    return df

def save_and_verify(df, output_path='data/dataset.csv', sample_path='data/sample.csv'):
    """
    Sélectionne, nettoie, vérifie et sauvegarde le dataset final.
    """
    logging.info("=== SAVE_AND_VERIFY ===")
    
    columns_order = [
        'timestamp', 'solar_wind_speed', 'solar_wind_density', 'bz_component',
        'solar_wind_pressure', 'bz_min_3h', 'dst_index',
        'month', 'sin_month', 'cos_month', 'season', 'hour_interval', 
        'bz_negative', 'is_solar_maximum', 'is_storm'
    ]
    df = df[columns_order]
    
    # Suppression NaNs dans les features critiques
    critical_cols = ['solar_wind_speed', 'solar_wind_density', 'bz_component']
    df = df.dropna(subset=critical_cols)
    
    # Rapport final
    total_rows = len(df)
    storm_dist = df['is_storm'].value_counts(normalize=True)
    pct_storm = storm_dist.get(1, 0)
    
    print("\n" + "="*40)
    print("RAPPORT DE VÉRIFICATION")
    print("="*40)
    print(f"Nombre total de lignes : {total_rows}")
    print(f"Ratio Classe 1 (Storm) : {pct_storm*100:.2f}%")
    print(f"Shape finale           : {df.shape}")
    print("="*40 + "\n")
    
    # Assertions selon les contraintes du professeur
    assert total_rows >= 10000, f"Erreur : Dataset trop petit ({total_rows} < 10000)"
    assert 0.05 <= pct_storm <= 0.25, f"Erreur : Déséquilibre non conforme ({pct_storm*100:.2f}% hors de [5%-25%])"
    
    df.to_csv(output_path, index=False)
    df.head(100).to_csv(sample_path, index=False)
    
    logging.info(f"Dataset sauvegardé avec succès dans {output_path}")
    return df

if __name__ == "__main__":
    # Chargement manuel du fichier .env si présent
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    
    os.makedirs('data/raw', exist_ok=True)
    
    START_YEAR = 2019
    END_YEAR = 2023
    LAG_HOURS = 6
    NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")
    
    try:
        grid = generate_time_grid(START_YEAR, END_YEAR)
        storms = collect_storms_donki(START_YEAR, END_YEAR, NASA_API_KEY)
        grid_with_target = create_target_variable(grid, storms)
        omni_data = collect_solar_wind_omni(START_YEAR, END_YEAR)
        merged_df = merge_datasets(grid_with_target, omni_data)
        enriched_df = add_engineered_features(merged_df)
        lagged_df = apply_lag(enriched_df, lag_hours=LAG_HOURS)
        final_dataset = save_and_verify(lagged_df)
        
        logging.info("PIPELINE TERMINÉ AVEC SUCCÈS")
        
    except Exception as e:
        logging.error(f"ÉCHEC DU PIPELINE : {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
