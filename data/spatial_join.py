import pandas as pd
import numpy as np

_EARTH_RADIUS_KM = 6371.0



def haversine_vectorized(lat1: float, lon1: float,
                         lats2: np.ndarray, lons2: np.ndarray) -> np.ndarray:
    """Calcule les distances en km entre un point de référence et un tableau de points GPS."""
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lats2 = np.radians(lats2)
    lons2 = np.radians(lons2)
    dlat = lats2 - lat1
    dlon = lons2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lats2) * np.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def _build_synop_index(synop_df: pd.DataFrame) -> pd.DataFrame:
    """Construit un index dédupliqué des stations SYNOP avec leur position GPS."""
    id_col = "station_id" if "station_id" in synop_df.columns else synop_df.columns[0]
    return (
        synop_df[[id_col, "lat", "lon"]]
        .drop_duplicates(subset=[id_col])
        .rename(columns={id_col: "synop_station_id"})
        .reset_index(drop=True)
    )


def find_nearest_synop(poll_lat: float, poll_lon: float,
                       synop_index: pd.DataFrame) -> dict:
    """Retourne la station SYNOP la plus proche d'un point GPS donné avec sa distance en km."""
    distances = haversine_vectorized(
        poll_lat, poll_lon,
        synop_index["lat"].values,
        synop_index["lon"].values,
    )
    idx = int(np.argmin(distances))
    row = synop_index.iloc[idx]
    return {
        "synop_station_id": row["synop_station_id"],
        "synop_lat": row["lat"],
        "synop_lon": row["lon"],
        "distance_km": round(distances[idx], 2),
    }


def join_pollution_synop(pollution_df: pd.DataFrame,
                         synop_df: pd.DataFrame,
                         max_distance_km: float = 50.0) -> pd.DataFrame:
    """Associe chaque station de pollution à la station SYNOP la plus proche dans le rayon donné.

    Les stations sans SYNOP dans le rayon reçoivent synop_station_id=None.
    """
    stations_poll = (
        pollution_df[["station_id", "lat", "lon"]]
        .dropna(subset=["lat", "lon"])
        .drop_duplicates(subset=["station_id"])
    )

    synop_index = _build_synop_index(synop_df)

    matches = stations_poll.apply(
        lambda row: find_nearest_synop(row["lat"], row["lon"], synop_index),
        axis=1,
        result_type="expand",
    )
    stations_poll = pd.concat([stations_poll.reset_index(drop=True), matches], axis=1)

    stations_poll.loc[stations_poll["distance_km"] > max_distance_km, "synop_station_id"] = None

    eloignees = stations_poll["synop_station_id"].isna().sum()
    if eloignees:
        print(f"[join] /!\\ {eloignees} stations pollution sans SYNOP dans {max_distance_km} km.")

    result = pollution_df.merge(
        stations_poll[["station_id", "synop_station_id", "synop_lat", "synop_lon", "distance_km"]],
        on="station_id",
        how="left",
    )

    print(f"[join] {result['synop_station_id'].notna().sum()}/{len(result)} mesures associées à une station SYNOP.")
    return result
