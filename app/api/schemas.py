from pydantic import BaseModel, Field
from typing import Literal

class StormFeatures(BaseModel):
    """
    Features nécessaires pour une prédiction de tempête géomagnétique.
    Seules les données physiques de base sont requises.
    """
    solar_wind_speed    : float = Field(..., ge=200,  le=1200, 
                                        description="Vitesse du vent solaire (km/s)",
                                        example=450.0)
    solar_wind_density  : float = Field(..., ge=0,    le=100,  
                                        description="Densité du vent solaire (n/cc)",
                                        example=5.2)
    bz_component        : float = Field(..., ge=-50,  le=30,   
                                        description="Composante Bz du champ magnétique (nT)",
                                        example=-12.5)
    dst_index           : float = Field(..., ge=-400, le=50,   
                                        description="Indice de perturbation magnétique (nT)",
                                        example=-45.0)
    month               : int   = Field(..., ge=1,    le=12,   
                                        description="Mois (1-12)",
                                        example=3)
    season              : Literal["hiver", "printemps", "ete", "automne"] = Field(
                                        ..., description="Saison",
                                        example="printemps")
    hour_interval       : str   = Field(..., 
                                        description="Tranche horaire (ex: '0h-3h')",
                                        example="6h-9h")
    is_solar_maximum    : int   = Field(..., ge=0, le=1,
                                        description="1 si année >= 2022",
                                        example=1)


class PredictionResponse(BaseModel):
    """Réponse retournée par /predict"""
    prediction  : str
    probability : float
    threshold   : float
    confidence  : str


class HealthResponse(BaseModel):
    """Réponse retournée par /health"""
    status      : str
    model_loaded: bool
