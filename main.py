import requests 
import time
import sys
import sqlite3
from datetime import datetime, date, timedelta

def interroger_endpoint(url):
    """ """
    try :
        response = requests.get(url, timeout=600)
        response.raise_for_status()
    
        try : 
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"erreur lors de la requête {e}")
        return None

def x_min(url, interval_minutes):
    """ """
    interval_seconds = interval_minutes * 60
    try :
        while True:
            print("nouvelle requête")
            data = interroger_endpoint(url)
            if data is not None:
                sauvegarder(data)
            else:
                print("aucune donnée reçue")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("arrêt demandé")
        sys.exit(0)

def sauvegarder(data):
    """ """
    con = sqlite3.connect("pollution.db")#nom de la db
    cursor = con.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mesures (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id  TEXT,
        station_name TEXT,
        lat    REAL,
        lon   REAL,
        indice      REAL,
        horaire     TEXT, 
        date        TEXT 
    )
    """)

    for station in data:
        api_date = datetime.fromisoformat(station.get("date"))
        cursor.execute(
        "INSERT INTO mesures (station_id, station_name, lat, lon, indice, horaire, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (station.get("station_id"), station.get("station_name"), station.get("lat"), station.get("lon"),
        station.get("indice"), api_date.strftime("%H:%M:%S"), api_date.strftime("%Y-%m-%d"))
    )
    con.commit()
    con.close()

def x_min_avec_date(interval_minutes):
    interval_seconds = interval_minutes * 60
    try:
        while True:
            print("nouvelle requête")
            hier = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"http://localhost:8000/index?date={hier}"
            data = interroger_endpoint(url)
            if data is not None:
                sauvegarder(data)
            else:
                print("aucune donnée reçue")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("arrêt demandé")
        sys.exit(0)

if __name__ == "__main__":
    url_init = "http://localhost:8000/init?days=10"#10 au départ
    print("initialisation de la base...")
    data_init = interroger_endpoint(url_init)
    if data_init is not None:
        sauvegarder(data_init)
        print("base initialisée")

    #url = "http://localhost:8001/indices" url fake_api
    #url = url de la fast api
    url = "http://localhost:8000/index"
    interval = 60
    #x_min(url, interval)
    x_min_avec_date(interval)