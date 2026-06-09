import io
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse

from app.api.schemas  import StormFeatures, PredictionResponse, HealthResponse
from app.api.model    import model, MODEL_METADATA, predict_single, predict_batch
from app.api.logger   import logger

app = FastAPI(
    title       = "AURORA API — Geomagnetic Storm Prediction",
    description = (
        "API de prédiction des tempêtes géomagnétiques avec 6h d'avance. "
        "Basée sur les données NASA OMNI2 et DONKI. "
        "Modèle : Random Forest + Undersampling."
    ),
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc"
)

@app.get("/", tags=["General"])
def home():
    logger.info("GET /")
    return {
        "project"      : "AURORA — Geomagnetic Storm Prediction",
        "description"  : "Prédiction des tempêtes géomagnétiques 6h à l'avance",
        "documentation": "http://localhost:8000/docs",
        "version"      : "1.0.0"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
def health():
    logger.info("GET /health")
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé — vérifiez models/final_model.joblib")
    return HealthResponse(status="ok", model_loaded=True)

@app.get("/model/info", tags=["Model"])
def model_info():
    logger.info("GET /model/info")
    return MODEL_METADATA

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(features: StormFeatures):
    """Prédiction unitaire — reçoit 13 features, retourne prediction + probabilité."""
    logger.info(f"POST /predict — bz={features.bz_component}, dst={features.dst_index}")
    try:
        result = predict_single(features.model_dump())
        return PredictionResponse(**result)
    except Exception as e:
        logger.error(f"Erreur /predict : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch", tags=["Prediction"])
def predict_batch_endpoint(file: UploadFile = File(...)):
    """Prédiction par lot — upload CSV, retourne CSV enrichi (prediction, probability, threshold)."""
    logger.info(f"POST /predict/batch — fichier : {file.filename}")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Fichier CSV requis (.csv)")

    try:
        contents = file.file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lecture CSV : {e}")

    # Vérification des colonnes requises
    required_cols = MODEL_METADATA["features"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Colonnes manquantes : {missing}")

    try:
        df_result = predict_batch(df)
    except Exception as e:
        logger.error(f"Erreur /predict/batch : {e}")
        raise HTTPException(status_code=500, detail=str(e))

    output = io.StringIO()
    df_result.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=predictions.csv"}
    )
