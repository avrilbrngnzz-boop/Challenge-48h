import numpy as np
import pandas as pd
from datetime import date, timedelta

from data.pipeline import get_index_for_date


def _get_daily_index(target_date: date) -> pd.DataFrame:
    """Exécute le pipeline complet pour une date et retourne l'indice moyen journalier par station."""
    index_df = get_index_for_date(target_date)
    daily = (
        index_df.groupby(["station_id", "station_name", "lat", "lon"])["indice_final"]
        .mean()
        .reset_index()
        .rename(columns={"indice_final": "indice_moyen"})
    )
    daily["date"] = target_date
    return daily


def build_forecast(reference_date: date | None = None,
                   lookback_days: int = 7,
                   horizon_days: int = 3) -> pd.DataFrame:
    """Prédit l'indice de pollution par régression linéaire pour les prochains jours.

    Collecte l'historique sur lookback_days jours, ajuste une droite par station (numpy.polyfit),
    puis projette sur horizon_days jours. Les stations avec moins de 2 points sont ignorées.
    Colonnes retournées : station_id, station_name, lat, lon, date, indice_prevu, tendance.
    """
    if reference_date is None:
        reference_date = date.today() - timedelta(days=1)

    dates = [reference_date - timedelta(days=i) for i in range(lookback_days - 1, -1, -1)]

    print(f"[forecast] Collecte des {lookback_days} derniers jours...")
    frames = []
    for d in dates:
        try:
            frames.append(_get_daily_index(d))
        except Exception as e:
            print(f"[forecast] /!\\ Données manquantes pour {d} : {e}")

    if not frames:
        return pd.DataFrame()

    history = pd.concat(frames, ignore_index=True)
    history["day_num"] = (pd.to_datetime(history["date"]) - pd.to_datetime(dates[0])).dt.days

    records = []
    for (station_id, station_name, lat, lon), group in history.groupby(
        ["station_id", "station_name", "lat", "lon"]
    ):
        group = group.dropna(subset=["indice_moyen"]).sort_values("day_num")
        if len(group) < 2:
            continue

        x = group["day_num"].values.astype(float)
        y = group["indice_moyen"].values.astype(float)
        coeffs = np.polyfit(x, y, 1)
        slope, intercept = coeffs

        last_day = int(x.max())
        for h in range(1, horizon_days + 1):
            future_day = last_day + h
            predicted = float(np.clip(slope * future_day + intercept, 0, 100))
            records.append({
                "station_id":   station_id,
                "station_name": station_name,
                "lat":          lat,
                "lon":          lon,
                "date":         (dates[0] + timedelta(days=future_day)).isoformat(),
                "indice_prevu": round(predicted, 1),
                "tendance":     round(float(slope), 4),
            })

    result = pd.DataFrame(records).sort_values(["date", "station_id"]).reset_index(drop=True)
    print(f"[forecast] {len(result)} prévisions générées pour {result['station_id'].nunique()} stations.")
    return result
