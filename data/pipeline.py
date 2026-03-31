from datetime import date

import pandas as pd

from data.extract_pollution import get_pollution_data
from data.extract_synop import get_meteo_data
from data.spatial_join import join_pollution_synop
from data.index_calculator import compute_index


def get_index_for_date(target_date: date) -> pd.DataFrame:
    """Exécute le pipeline complet pour une date et retourne les indices par station et horodatage.

    Colonnes retournées : station_id, station_name, lat, lon, date_debut,
    indice_pollution, modificateur_meteo, indice_final, synop_station_id.
    """
    pollution_df = get_pollution_data(target_date)
    synop_df = get_meteo_data(target_date)

    joined = join_pollution_synop(pollution_df, synop_df, max_distance_km=100.0)

    synop_daily = (
        synop_df.groupby("station_id")[["ff", "u"]]
        .mean()
        .reset_index()
        .rename(columns={"station_id": "synop_station_id"})
    )

    merged = joined.merge(synop_daily, on="synop_station_id", how="left")
    return compute_index(merged)
