import os
import requests
import time
import sys
import sqlite3
from datetime import datetime, date, timedelta

DATA_API_URL = os.environ.get("DATA_API_URL", "http://localhost:8000")
DB_PATH      = os.environ.get("DB_PATH", "pollution.db")


def interroger_endpoint(url):
    """Appelle un endpoint HTTP et retourne le JSON ou None en cas d'erreur."""
    try:
        response = requests.get(url, timeout=600)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return response.text
    except requests.exceptions.RequestException as e:
        print(f"erreur lors de la requête {e}")
        return None


def sauvegarder(data):
    """Insère les données dans la BDD SQLite (ignore les doublons)."""
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mesures (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id   TEXT,
        station_name TEXT,
        lat          REAL,
        lon          REAL,
        indice       REAL,
        horaire      TEXT,
        date         TEXT,
        UNIQUE(station_id, date)
    )
    """)

    for station in data:
        api_date = datetime.fromisoformat(station.get("date"))
        cursor.execute(
            "INSERT OR IGNORE INTO mesures (station_id, station_name, lat, lon, indice, horaire, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                station.get("station_id"),
                station.get("station_name"),
                station.get("lat"),
                station.get("lon"),
                station.get("indice"),
                api_date.strftime("%H:%M:%S"),
                api_date.strftime("%Y-%m-%d"),
            ),
        )
    con.commit()
    con.close()


def x_min_avec_date(interval_minutes):
    """Boucle infinie : interroge /index toutes les interval_minutes minutes et sauvegarde."""
    interval_seconds = interval_minutes * 60
    try:
        while True:
            print("nouvelle requête")
            hier = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"{DATA_API_URL}/index?date={hier}"
            data = interroger_endpoint(url)
            if data is not None:
                sauvegarder(data)
            else:
                print("aucune donnée reçue")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("arrêt demandé")
        sys.exit(0)


def db_est_vide():
    """Retourne True si la table mesures est vide ou n'existe pas."""
    try:
        con = sqlite3.connect(DB_PATH)
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM mesures")
        count = cursor.fetchone()[0]
        con.close()
        return count == 0
    except Exception:
        return True


if __name__ == "__main__":
    if db_est_vide():
        url_init = f"{DATA_API_URL}/init?days=10"
        print("initialisation de la base...")
        data_init = interroger_endpoint(url_init)
        if data_init is not None:
            sauvegarder(data_init)
            print("base initialisée")
    else:
        print("base déjà initialisée")

    interval = 60
    x_min_avec_date(interval)
