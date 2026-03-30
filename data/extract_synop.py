import requests
import pandas as pd
from datetime import date, timedelta
from io import BytesIO
import gzip

_BASE_URL = (
    "https://object.files.data.gouv.fr/meteofrance/data"
    "/synchro_ftp/OBS/SYNOP/synop_{year}.csv.gz"
)

_CACHE: dict[int, pd.DataFrame] = {}

_COLS_BRUT = {
    "geo_id_wmo":    "station_id",
    "lat":           "lat",
    "lon":           "lon",
    "validity_time": "date_debut",
    "ff":            "ff",
    "u":             "u",
    "t":             "t",
    "pmer":          "pmer",
}


def _fetch_synop(year: int) -> pd.DataFrame:
    """Télécharge le fichier SYNOP annuel compressé depuis Météo-France. Résultat mis en cache par année."""
    if year in _CACHE:
        return _CACHE[year]
    url = _BASE_URL.format(year=year)
    print(f"[synop] Téléchargement {url}...")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with gzip.open(BytesIO(resp.content)) as f:
        df = pd.read_csv(f, sep=";", low_memory=False)
    _CACHE[year] = df
    return df


def _clean(df: pd.DataFrame, target_date: date) -> pd.DataFrame:
    """Filtre les observations SYNOP pour la date cible et convertit les unités (K→°C, Pa→hPa)."""
    cols_dispo = {k: v for k, v in _COLS_BRUT.items() if k in df.columns}
    df = df[list(cols_dispo.keys())].rename(columns=cols_dispo)

    df["date_debut"] = pd.to_datetime(df["date_debut"], utc=True, errors="coerce")
    df = df.dropna(subset=["date_debut"])
    df = df[df["date_debut"].dt.date == target_date].copy()
    df["date_debut"] = df["date_debut"].dt.tz_localize(None)

    if "t" in df.columns:
        df["t"] = pd.to_numeric(df["t"], errors="coerce") - 273.15
    if "pmer" in df.columns:
        df["pmer"] = pd.to_numeric(df["pmer"], errors="coerce") / 100.0
    for col in ["ff", "u"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["station_id", "lat", "lon"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    return df.reset_index(drop=True)


def get_meteo_data(target_date: date | None = None) -> pd.DataFrame:
    """Retourne les observations météo SYNOP pour la date donnée.

    Colonnes retournées : station_id, lat, lon, date_debut, ff (vent m/s), u (humidité %), t (°C), pmer (hPa).
    Par défaut, utilise la veille.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    raw = _fetch_synop(target_date.year)

    print(f"[synop] Filtrage sur {target_date}...")
    clean = _clean(raw, target_date)
    print(f"[synop] {len(clean)} observations valides — {clean['station_id'].nunique()} stations.")

    return clean[["station_id", "lat", "lon", "date_debut", "ff", "u", "t", "pmer"]]
