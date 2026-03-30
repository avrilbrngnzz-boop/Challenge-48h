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

# URL de l'API tabulaire data.gouv.fr pour les métadonnées stations (GPS)
_STATIONS_RESOURCE_ID = "eb87c56c-dea9-4377-a1e7-03ada59d3043"
_TABULAR_API = "https://tabular-api.data.gouv.fr/api/resources/{resource_id}/data/"

# Polluants cibles et leurs codes LCSQA
POLLUANTS_CIBLES = {"NO2", "PM10", "PM2.5", "O3", "SO2", "CO"}

# Colonnes réelles du CSV LCSQA (séparateur ';', valeurs entre guillemets)
_COLS_BRUT = {
    "code site": "station_id",
    "nom site": "station_name",
    "Polluant": "polluant",
    "Date de début": "date_debut",
    "valeur": "valeur",
    "unité de mesure": "unite",
    "validité": "validite",
}


# 1. Téléchargement CSV journalier

def _fetch_csv(target_date: date) -> pd.DataFrame:
    key = _KEY_TEMPLATE.format(year=target_date.year, date=target_date.isoformat())
    url = _MINIO_DOWNLOAD.format(key=key.replace("/", "%2F"))
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    # Séparateur ';', valeurs entre guillemets, encodage UTF-8 avec BOM
    df = pd.read_csv(
        StringIO(resp.content.decode("utf-8-sig")),
        sep=";",
        quotechar='"',
        low_memory=False,
    )
    return df



# 2. Nettoyage

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    # Garder uniquement les colonnes utiles et les renommer
    cols_disponibles = {k: v for k, v in _COLS_BRUT.items() if k in df.columns}
    df = df[list(cols_disponibles.keys())].rename(columns=cols_disponibles)

    # Garder uniquement les mesures valides (validite == "1" en string dans le CSV)
    df = df[df["validite"].astype(str).str.strip() == "1"].copy()

    # Garder uniquement les polluants ciblés
    df = df[df["polluant"].isin(POLLUANTS_CIBLES)].copy()

    # Convertir la date
    df["date_debut"] = pd.to_datetime(df["date_debut"], format="%Y/%m/%d %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["date_debut"])

    # Convertir la valeur en float, supprimer les NaN
    df["valeur"] = pd.to_numeric(df["valeur"].astype(str).str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["valeur"])
    df = df[df["valeur"] >= 0]

    return df.reset_index(drop=True)


# 3. Métadonnées stations (GPS)

def _fetch_stations_gps() -> pd.DataFrame:
    """
    Récupère les coordonnées GPS des stations via l'API tabulaire data.gouv.fr.
    On garde uniquement les stations actives (OperationalActivityEnd vide).
    """
    rows = []
    page = 1
    page_size = 100  # max accepté par l'API tabulaire data.gouv.fr

    while True:
        url = _TABULAR_API.format(resource_id=_STATIONS_RESOURCE_ID)
        resp = requests.get(url, params={"page": page, "page_size": page_size}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("data", [])
        if not batch:
            break

        for row in batch:
            # station_id = partie après 'STA-' dans le champ Broader
            broader = row.get("Broader", "") or ""
            station_id = broader.split("/STA-")[-1] if "/STA-" in broader else None

            end = row.get("OperationalActivityEnd", "")
            if end:  # station fermée
                continue

            lat = row.get("Latitude")
            lon = row.get("Longitude")
            if station_id and lat and lon:
                rows.append({
                    "station_id": station_id,
                    "lat": float(lat),
                    "lon": float(lon),
                })

        if len(batch) < page_size:
            break
        page += 1

    gps_df = pd.DataFrame(rows).drop_duplicates(subset=["station_id"])
    return gps_df


# 4. Interface publique

def get_pollution_data(target_date: date | None = None) -> pd.DataFrame:
    """
    Retourne un DataFrame propre des mesures de pollution pour une date donnée.
    Colonnes résultantes :
        station_id  | station_name | polluant | date_debut
        valeur      | unite        | lat      | lon
        
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    print(f"[pollution] Téléchargement des données pour {target_date}...")
    raw = _fetch_csv(target_date)

    print(f"[pollution] {len(raw)} lignes brutes, nettoyage en cours...")
    clean = _clean(raw)
    print(f"[pollution] {len(clean)} mesures valides après nettoyage.")

    # Enrichissement GPS
    print("[pollution] Récupération des coordonnées GPS des stations...")
    gps = _fetch_stations_gps()
    print(f"[pollution] {len(gps)} stations actives trouvées.")

    merged = clean.merge(gps, on="station_id", how="left")

    # Stations sans GPS : on les garde mais on log un warning
    sans_gps = merged["lat"].isna().sum()
    if sans_gps:
        print(f"[pollution] /!\\ {sans_gps} mesures sans coordonnees GPS (stations inconnues).")

    return merged[[
        "station_id", "station_name", "polluant",
        "date_debut", "valeur", "unite", "lat", "lon"
    ]]


if __name__ == "__main__":
    df = get_pollution_data()
    print(df.head(10).to_string())
    print(f"\nShape : {df.shape}")
    print(f"Polluants présents : {df['polluant'].unique()}")
    print(f"Stations avec GPS : {df['lat'].notna().sum()}/{len(df)}")
