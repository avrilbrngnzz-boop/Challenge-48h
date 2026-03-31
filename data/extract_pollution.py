import requests
import pandas as pd
from datetime import date, timedelta
from io import StringIO

_MINIO_DOWNLOAD = (
    "https://object.infra.data.gouv.fr/api/v1/buckets/ineris-prod/objects/download"
    "?prefix={key}&version_id="
)
_KEY_TEMPLATE = (
    "lcsqa/concentrations-de-polluants-atmospheriques-reglementes"
    "/temps-reel/{year}/FR_E2_{date}.csv"
)

_STATIONS_RESOURCE_ID = "eb87c56c-dea9-4377-a1e7-03ada59d3043"
_TABULAR_API = "https://tabular-api.data.gouv.fr/api/resources/{resource_id}/data/"

POLLUANTS_CIBLES = {"NO2", "PM10", "PM2.5", "O3", "SO2", "CO"}

_COLS_BRUT = {
    "code site": "station_id",
    "nom site": "station_name",
    "Polluant": "polluant",
    "Date de début": "date_debut",
    "valeur": "valeur",
    "unité de mesure": "unite",
    "validité": "validite",
}


def _fetch_csv(target_date: date) -> pd.DataFrame:
    """Télécharge le fichier CSV brut LCSQA depuis MinIO pour la date donnée."""
    key = _KEY_TEMPLATE.format(year=target_date.year, date=target_date.isoformat())
    url = _MINIO_DOWNLOAD.format(key=key.replace("/", "%2F"))
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(
        StringIO(resp.content.decode("utf-8-sig")),
        sep=";",
        quotechar='"',
        low_memory=False,
    )
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Filtre les mesures valides, sélectionne les polluants cibles et normalise les types."""
    cols_disponibles = {k: v for k, v in _COLS_BRUT.items() if k in df.columns}
    df = df[list(cols_disponibles.keys())].rename(columns=cols_disponibles)
    df = df[df["validite"].astype(str).str.strip() == "1"].copy()
    df = df[df["polluant"].isin(POLLUANTS_CIBLES)].copy()
    df["date_debut"] = pd.to_datetime(df["date_debut"], format="%Y/%m/%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["date_debut"])
    df["valeur"] = pd.to_numeric(df["valeur"].astype(str).str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["valeur"])
    df = df[df["valeur"] >= 0]
    return df.reset_index(drop=True)


def _fetch_stations_gps() -> pd.DataFrame:
    """Récupère les coordonnées GPS de toutes les stations actives via l'API tabulaire data.gouv.fr."""
    rows = []
    page = 1
    page_size = 100

    while True:
        url = _TABULAR_API.format(resource_id=_STATIONS_RESOURCE_ID)
        resp = requests.get(url, params={"page": page, "page_size": page_size}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("data", [])
        if not batch:
            break

        for row in batch:
            broader = row.get("Broader", "") or ""
            station_id = broader.split("/STA-")[-1] if "/STA-" in broader else None
            if row.get("OperationalActivityEnd", ""):
                continue
            lat = row.get("Latitude")
            lon = row.get("Longitude")
            if station_id and lat and lon:
                rows.append({"station_id": station_id, "lat": float(lat), "lon": float(lon)})

        if len(batch) < page_size:
            break
        page += 1

    return pd.DataFrame(rows).drop_duplicates(subset=["station_id"])


def get_pollution_data(target_date: date | None = None) -> pd.DataFrame:
    """Retourne les mesures de pollution valides avec coordonnées GPS pour la date donnée.

    Colonnes retournées : station_id, station_name, polluant, date_debut, valeur, unite, lat, lon.
    Par défaut, utilise la veille.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    print(f"[pollution] Téléchargement des données pour {target_date}...")
    raw = _fetch_csv(target_date)

    print(f"[pollution] {len(raw)} lignes brutes, nettoyage en cours...")
    clean = _clean(raw)
    print(f"[pollution] {len(clean)} mesures valides après nettoyage.")

    print("[pollution] Récupération des coordonnées GPS des stations...")
    gps = _fetch_stations_gps()
    print(f"[pollution] {len(gps)} stations actives trouvées.")

    merged = clean.merge(gps, on="station_id", how="left")

    sans_gps = merged["lat"].isna().sum()
    if sans_gps:
        print(f"[pollution] /!\\ {sans_gps} mesures sans coordonnees GPS (stations inconnues).")

    return merged[["station_id", "station_name", "polluant", "date_debut", "valeur", "unite", "lat", "lon"]]
