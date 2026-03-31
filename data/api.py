from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, timedelta
import pandas as pd

from data.pipeline import get_index_for_date
from data.forecast import build_forecast

app = FastAPI(
    title="Indice Pollution + Météo",
    description="API exposant l'indice combiné pollution atmosphérique et météo par station.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _nan_to_none(v):
    try:
        return None if pd.isna(v) else v
    except (TypeError, ValueError):
        return v


def _build_response(df: pd.DataFrame) -> list[dict]:
    records = []
    for _, row in df.iterrows():
        records.append({
            "station_id":         row["station_id"],
            "station_name":       row["station_name"],
            "lat":                _nan_to_none(row["lat"]),
            "lon":                _nan_to_none(row["lon"]),
            "date":               row["date_debut"].isoformat() if pd.notna(row["date_debut"]) else None,
            "indice":             _nan_to_none(row["indice_final"]),
            "indice_pollution":   _nan_to_none(row["indice_pollution"]),
            "modificateur_meteo": _nan_to_none(row["modificateur_meteo"]),
            "synop_station_id":   _nan_to_none(row.get("synop_station_id")),
        })
    return records


@app.get("/index", summary="Indice combiné par station pour une date")
def get_index(
    target_date: date = Query(
        default=None,
        alias="date",
        description="Date au format YYYY-MM-DD (défaut : hier)",
        examples=["2026-03-29"],
    )
):
    """
    Retourne la liste des indices combinés pollution+météo pour toutes les stations.

    **Réponse JSON :**
    ```json
    [
      {
        "station_id": "FR01011",
        "station_name": "Metz-Centre",
        "lat": 49.119442,
        "lon": 6.180833,
        "date": "2026-03-29T00:00:00",
        "indice": 42.3,
        "indice_pollution": 45.0,
        "modificateur_meteo": 0.94,
        "synop_station_id": "07083"
      }
    ]
    ```
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    if target_date > date.today():
        raise HTTPException(status_code=400, detail="La date ne peut pas être dans le futur.")

    try:
        df = get_index_for_date(target_date)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur récupération données : {e}")

    if df.empty:
        raise HTTPException(status_code=404, detail=f"Aucune donnée pour le {target_date}.")

    return _build_response(df)


@app.get("/forecast", summary="Prévisions par régression linéaire")
def get_forecast(
    reference_date: date = Query(
        default=None,
        alias="date",
        description="Date de référence YYYY-MM-DD (défaut : hier)",
        examples=["2026-03-29"],
    ),
    lookback: int = Query(default=7, ge=2, le=30, description="Nombre de jours historiques"),
    horizon: int = Query(default=3, ge=1, le=7, description="Nombre de jours à prévoir"),
):
    """
    Prévisions de l'indice par régression linéaire simple.

    **Réponse JSON :**
    ```json
    [
      {
        "station_id": "FR01011",
        "station_name": "Metz-Centre",
        "lat": 49.119442,
        "lon": 6.180833,
        "date": "2026-04-01",
        "indice_prevu": 38.5,
        "tendance": -1.2
      }
    ]
    ```
    `tendance` : variation de l'indice par jour (négatif = amélioration).
    """
    if reference_date is None:
        reference_date = date.today() - timedelta(days=1)

    try:
        df = build_forecast(reference_date, lookback_days=lookback, horizon_days=horizon)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur calcul prévisions : {e}")

    if df.empty:
        raise HTTPException(status_code=404, detail="Pas assez de données pour calculer des prévisions.")

    return df.to_dict(orient="records")


@app.get("/init", summary="Initialisation BDD — historique N jours")
def get_init(
    days: int = Query(default=10, ge=1, le=30, description="Nombre de jours d'historique à récupérer"),
):
    """
    Retourne l'historique des indices pour les N derniers jours.

    Destiné à l'**initialisation de la base de données** backend.
    À n'appeler qu'une seule fois au démarrage — utiliser `/index` pour les mises à jour courantes.

    **Réponse JSON :** même structure que `/index`, tous jours confondus.
    """
    today = date.today()
    all_records: list[dict] = []

    for delta in range(1, days + 1):
        target = today - timedelta(days=delta)
        try:
            df = get_index_for_date(target)
            if not df.empty:
                all_records.extend(_build_response(df))
        except Exception:
            continue

    return all_records


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return {"message": "API Indice Pollution+Météo — voir /docs pour la documentation."}
