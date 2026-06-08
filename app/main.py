import io
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from app.schemas  import StormFeatures, PredictionResponse, HealthResponse
from app.model    import model, MODEL_METADATA, predict_single, predict_batch
from app.logger   import logger

# ============================================================
# Initialisation de l'application FastAPI
# ============================================================
app = FastAPI(
    title       = "AURORA API — Geomagnetic Storm Prediction",
    description = (
        "API de prédiction des tempêtes géomagnétiques avec 6h d'avance. "
        "Basée sur les données NASA OMNI2 et DONKI. "
        "Modèle : Random Forest + Undersampling."
    ),
    version     = "1.0.0",
    docs_url    = "/docs",   # URL Swagger UI
    redoc_url   = "/redoc"
)

# ============================================================
# Endpoint 1 : Page d'accueil
# ============================================================
@app.get("/", tags=["General"])
def home():
    """Page d'accueil avec lien vers la documentation Swagger."""
    logger.info("GET / — accueil")
    return {
        "project"      : "AURORA — Geomagnetic Storm Prediction",
        "description"  : "Prédiction des tempêtes géomagnétiques 6h à l'avance",
        "documentation": "http://localhost:8000/docs",
        "version"      : "1.0.0"
    }

# ============================================================
# Endpoint 2 : Health check
# ============================================================
@app.get("/health", response_model=HealthResponse, tags=["General"])
def health():
    """
    Vérifie que l'API et le modèle sont opérationnels.
    Retourne 200 OK si tout va bien, 503 si le modèle n'est pas chargé.
    """
    logger.info("GET /health")
    model_loaded = model is not None

    if not model_loaded:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé — vérifiez models/final_model.joblib"
        )

    return HealthResponse(status="ok", model_loaded=True)

# ============================================================
# Endpoint 3 : Métadonnées du modèle
# ============================================================
@app.get("/model/info", tags=["Model"])
def model_info():
    """
    Retourne les métadonnées du modèle :
    type, version, date d'entraînement, métriques, seuil utilisé.
    """
    logger.info("GET /model/info")
    return MODEL_METADATA

# ============================================================
# Endpoint 4 : Prédiction unitaire
# ============================================================
@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(features: StormFeatures):
    """
    Prédiction pour un seul cas.
    Reçoit les 13 features physiques, retourne la prédiction + probabilité.
    """
    logger.info(f"POST /predict — features reçues : bz={features.bz_component}, dst={features.dst_index}")

    try:
        # ".model_dump()" convertit l'objet Pydantic validé en dictionnaire classique
        result = predict_single(features.model_dump())
        return PredictionResponse(**result)
    except Exception as e:
        logger.error(f"Erreur /predict : {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# Endpoint 5 : Prédiction par lot (batch)
# ============================================================
@app.post("/predict/batch", tags=["Prediction"])
def predict_batch_endpoint(file: UploadFile = File(...)):
    """
    Prédiction par lot.
    Reçoit un fichier CSV avec les features, retourne un CSV enrichi
    avec les colonnes : prediction, probability, threshold.
    """
    logger.info(f"POST /predict/batch — fichier reçu : {file.filename}")

    # Vérification stricte du type de fichier
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être au format CSV"
        )

    try:
        contents = file.file.read()
        df       = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lecture CSV : {e}")

    # Vérification des colonnes requises
    required_cols = MODEL_METADATA["features"]
    missing       = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Colonnes manquantes dans le CSV : {missing}"
        )

    try:
        df_result = predict_batch(df[required_cols])
    except Exception as e:
        logger.error(f"Erreur /predict/batch : {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Retourner le CSV enrichi en streaming (l'utilisateur télécharge le fichier de résultats en retour)
    output = io.StringIO()
    df_result.to_csv(output, index=False)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions.csv"}
    )
