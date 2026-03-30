import pandas as pd
import numpy as np

_SEUILS = {
    "NO2":  200.0,
    "PM10":  50.0,
    "PM2.5": 25.0,
    "O3":   120.0,
    "SO2":  350.0,
    "CO":  10000.0,
}

_POIDS = {
    "PM2.5": 0.35,
    "PM10":  0.25,
    "NO2":   0.20,
    "O3":    0.10,
    "SO2":   0.05,
    "CO":    0.05,
}


def _sous_indice(polluant: str, valeur: float) -> float:
    """Calcule le sous-indice normalisé (0–100) d'un polluant par rapport à son seuil réglementaire."""
    seuil = _SEUILS.get(polluant)
    if seuil is None or pd.isna(valeur):
        return np.nan
    return min((valeur / seuil) * 100, 100.0)


def _indice_pollution(group: pd.DataFrame) -> float:
    """Calcule l'indice pollution pondéré pour un groupe de mesures d'une même station/heure."""
    total_poids = 0.0
    total_valeur = 0.0
    for _, row in group.iterrows():
        p = row["polluant"]
        poids = _POIDS.get(p, 0.0)
        si = _sous_indice(p, row["valeur"])
        if not np.isnan(si) and poids > 0:
            total_valeur += si * poids
            total_poids += poids
    if total_poids == 0:
        return np.nan
    return total_valeur / total_poids


def _modificateur_meteo(ff=None, u=None) -> float:
    """Calcule le modificateur météo à partir du vent (ff) et de l'humidité (u).

    Vent fort → indice réduit (dispersion). Humidité élevée → indice augmenté (concentration).
    Résultat borné entre 0.5 et 1.5.
    """
    modificateur = 1.0
    if ff is not None and not pd.isna(ff):
        facteur_vent = 1.0 - (min(float(ff), 10.0) / 10.0) * 0.4
        modificateur *= facteur_vent
    if u is not None and not pd.isna(u):
        facteur_hum = 1.0 + max(0.0, (float(u) - 70.0) / 100.0) * 0.3
        modificateur *= facteur_hum
    return round(np.clip(modificateur, 0.5, 1.5), 4)


def compute_index(merged_df: pd.DataFrame) -> pd.DataFrame:
    """Calcule l'indice final combiné pollution+météo pour chaque station et horodatage.

    Colonnes retournées : station_id, station_name, lat, lon, date_debut,
    indice_pollution, modificateur_meteo, indice_final (0–100).
    """
    cols_meteo_dispo = {
        "ff": "ff" in merged_df.columns,
        "u":  "u"  in merged_df.columns,
    }

    records = []
    for (station_id, date_debut), group in merged_df.groupby(["station_id", "date_debut"]):
        row0 = group.iloc[0]
        ip = _indice_pollution(group)
        ff_val = row0.get("ff") if cols_meteo_dispo["ff"] else None
        u_val  = row0.get("u")  if cols_meteo_dispo["u"]  else None
        mod    = _modificateur_meteo(ff=ff_val, u=u_val)
        indice_final = round(np.clip(ip * mod, 0, 100), 1) if not np.isnan(ip) else None

        record = {
            "station_id":         station_id,
            "station_name":       row0.get("station_name", ""),
            "lat":                row0.get("lat"),
            "lon":                row0.get("lon"),
            "date_debut":         date_debut,
            "indice_pollution":   round(ip, 1) if not np.isnan(ip) else None,
            "modificateur_meteo": mod,
            "indice_final":       indice_final,
        }
        if "synop_station_id" in merged_df.columns:
            record["synop_station_id"] = row0.get("synop_station_id")
        records.append(record)

    result = pd.DataFrame(records).sort_values(["date_debut", "station_id"]).reset_index(drop=True)
    print(f"[index] {len(result)} indices calculés ({result['indice_final'].notna().sum()} valides).")
    return result
